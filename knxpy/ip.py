import socket
import asyncio

import logging

from . import util



class KNXIPFrame():
    
    SEARCH_REQUEST                  = 0x0201
    SEARCH_RESPONSE                 = 0x0202
    DESCRIPTION_REQUEST             = 0x0203
    DESCRIPTION_RESPONSE            = 0x0204
    CONNECT_REQUEST                 = 0x0205
    CONNECT_RESPONSE                = 0x0206
    CONNECTIONSTATE_REQUEST         = 0x0207
    CONNECTIONSTATE_RESPONSE        = 0x0208
    DISCONNECT_REQUEST              = 0x0209
    DISCONNECT_RESPONSE             = 0x020a
    DEVICE_CONFIGURATION_REQUEST    = 0x0310
    DEVICE_CONFIGURATION_ACK        = 0x0111
    TUNNELING_REQUEST               = 0x0420
    TUNNELLING_ACK                  = 0x0421
    ROUTING_INDICATION              = 0x0530
    ROUTING_LOST_MESSAGE            = 0x0531
    
    DEVICE_MGMT_CONNECTION          = 0x03
    TUNNEL_CONNECTION               = 0x04
    REMLOG_CONNECTION               = 0x06
    REMCONF_CONNECTION              = 0x07
    OBJSVR_CONNECTION               = 0x08
    
    E_NO_ERROR                      = 0x00
    E_HOST_PROTOCOL_TYPE            = 0x01
    E_VERSION_NOT_SUPPORTED         = 0x02
    E_SEQUENCE_NUMBER               = 0x04
    E_CONNECTION_ID                 = 0x21
    E_CONNECTION_TYPE               = 0x22
    E_CONNECTION_OPTION             = 0x23
    E_NO_MORE_CONNECTIONS           = 0x24
    E_DATA_CONNECTION               = 0x26
    E_KNX_CONNECTION                = 0x27
    E_TUNNELING_LAYER               = 0x28
    
    body = None
    
    def __init__(self, service_type_id):
        self.service_type_id = service_type_id
    
    def to_frame(self):
        return self.header() + self.body
    
    @classmethod
    def from_frame(cls, frame):
        # TODO: Check length
        p = cls(frame[2]*256 + frame[3])
        p.body = frame[6:]
        return p
        
    def total_length(self):
        return 6 + len(self.body)
    
    def header(self):
        tl = self.total_length()
        res = bytearray([0x06,0x10,0,0,0,0])
        res[2] = (self.service_type_id >> 8) & 0xff
        res[3] = (self.service_type_id >> 0) & 0xff
        res[4] = (tl >> 8) & 0xff
        res[5] = (tl >> 0) & 0xff
        return res
    


class KNXTunnelingRequest:
    
    seq = 0
    cEmi = None
    channel = 0
    
    def __init__(self):
        pass
        
    @classmethod
    def from_body(cls, body):
        # TODO: Check length
        p = cls()
        p.channel = body[1]
        p.seq = body[2]
        p.cEmi = body[4:]
        return p
    
    def __str__(self):
        return ""

class CEMIMessage():
    
    CMD_GROUP_READ = 1
    CMD_GROUP_WRITE = 2
    CMD_GROUP_RESPONSE = 3
    CMD_UNKNOWN = 0xff
    
    code = 0
    ctl1 = 0
    ctl2 = 0
    src_addr = None
    dst_addr = None
    cmd = None
    tpci_apci = 0
    mpdu_len = 0
    data = [0]
    
    def __init__(self):
        pass    
    
    @classmethod
    def from_body(cls, cemi):

        # TODO: check that length matches
        m = cls()
        m.code = cemi[0]
        offset = cemi[1]
        
        m.ctl1 = cemi[2+offset]
        m.ctl2 = cemi[3+offset]
        
        m.src_addr = cemi[4+offset]*256+cemi[5+offset]
        m.dst_addr = cemi[6+offset]*256+cemi[7+offset]
    
        m.mpdu_len = cemi[8+offset]
        
        tpci_apci = cemi[9+offset]*256+cemi[10+offset]
        apci = tpci_apci & 0x3ff
        
        # for APCI codes see KNX Standard 03/03/07 Application layer 
        # table Application Layer control field
        if (apci & 0x080):
            # Group write
            m.cmd = CEMIMessage.CMD_GROUP_WRITE
        elif (apci == 0):
            m.cmd = CEMIMessage.CMD_GROUP_READ
        elif (apci & 0x40):
            m.cmd = CEMIMessage.CMD_GROUP_RESPONSE
        else:
            m.cmd = CEMIMessage.CMD_NOT_IMPLEMENTED
        
        apdu = cemi[10+offset:]
        if len(apdu) != m.mpdu_len:
            raise Exception("APDU LEN should be {} but is {}".format(m.mpdu_len,len(apdu)))
        
        if len(apdu)==1:
            m.data = apci & 0x2f
        else:
            m.data = cemi[11+offset:]
        
        return m
    
    def init_group(self,dst_addr=1):
        self.code = 0x11 # Comes from packet dump, why?
        self.ctl1 = 0xbc # frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0, confirm-flag 0
        self.ctl2 = 0xe0 # dst addr type 1, hop count 6, extended frame format
        self.src_addr = 0
        self.dst_addr = dst_addr
    
    def init_group_write(self, dst_addr=1, data=0):
        self.init_group(dst_addr)
        self.tpci_apci = 0x00 * 256 + 0x80 # unnumbered data packet, group write
        self.data = data
    
    def init_group_read(self, dst_addr=1):
        self.init_group(dst_addr)
        self.tpci_apci = 0x00 # unnumbered data packet, group read
        self.data = 0

    def to_body(self):
        b = [self.code,0x00,self.ctl1,self.ctl2,
             (self.src_addr >> 8) & 0xff, (self.src_addr >> 0) & 0xff,
             (self.dst_addr >> 8) & 0xff, (self.dst_addr >> 0) & 0xff,
             ]


        if type(self.data)==list:
            data = self.data
        else:
            data = [self.data]

        if (len(data)==1) and ((data[0] & 3) == data[0]) :
            # less than 6 bit of data, pack into APCI byte
            b.extend([1,(self.tpci_apci >> 8) & 0xff,((self.tpci_apci >> 0) & 0xff) + data[0]])
        
        else:
            b.extend([1+len(data),(self.tpci_apci >> 8) & 0xff,(self.tpci_apci >> 0) & 0xff])
            b.extend(data)

        return b
        
    def __str__(self):
        
        c="??"
        if self.cmd == self.CMD_GROUP_READ:
            c = "RD"
        elif self.cmd == self.CMD_GROUP_WRITE:
            c = "WR"
        elif self.cmd == self.CMD_GROUP_RESPONSE:
            c = "RS"
        return "{0:<10}-> {1:<10} {2} {3}".format(util.decode_ga(self.src_addr), util.decode_ga(self.dst_addr), c, self.data)
    
    
class KNXIPTunnel():
    """
    An IP tunnel to the KNX bus to send and recieve data

    """

    data_server = None
    control_socket = None
    channel = 0
    seq = 0
    data_handler = None
    result_queue = None
    
    def __init__(self, ip, port,loop):
        self.remote_ip = ip
        self.remote_port = port
        self.discovery_port = None
        self.data_port = None
        self.read_queue = []
        self.result_queue = asyncio.Queue()
        self.unack_queue = asyncio.Queue()
        self.loop = loop

    async def connect(self):
        """
        Connect to the KNX bus

        Examples
        --------
        >>> import asyncio
        >>> import knxpy
        >>> async def main(loop):
        ...     tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
        ...     await tunnel.connect()
        ...
        >>> loop = asyncio.get_event_loop()
        >>> loop.run_until_complete(main(loop))

        """
        # Find my own IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.remote_ip,self.remote_port))
        local_ip=s.getsockname()[0]

        if self.data_server:
            logging.info("Data server already running, not starting again")
        else:
            listen = self.loop.create_datagram_endpoint(DataServerProtocol, local_addr=(local_ip, 0))
            transport, protocol = await listen
            transport.tunnel = self

            self.data_server = transport
            # get the data port
            self.data_port = transport.get_extra_info('sockname')[1]


        ################################################################################
        # Send a message to the knx ip interface to instruct it to send bus telegrams
        # to the data server

        control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        control_socket.bind((local_ip, 0))

        # Connect packet
        p=bytearray()
        p.extend([0x06,0x10]) # header size, protocol version
        p.extend(util.int_to_array(KNXIPFrame.CONNECT_REQUEST , 2))
        p.extend([0x00,0x1a]) # total length = 24 octet

        # Control endpoint
        p.extend([0x08,0x01]) # length 8 bytes, UPD
        _ip,port=control_socket.getsockname()
        p.extend(util.ip_to_array(local_ip))
        p.extend(util.int_to_array(port, 2)) 

        # Data endpoint
        p.extend([0x08,0x01]) # length 8 bytes, UPD
        p.extend(util.ip_to_array(local_ip))
        p.extend(util.int_to_array(self.data_port, 2)) 

        # 
        p.extend([0x04,0x04,0x02,0x00])
        control_socket.sendto(p, (self.remote_ip, self.remote_port))

        #TODO: non-blocking receive
        received = control_socket.recv(1024)
        received = bytearray(received)

        r_sid = received[2]*256+received[3]
        if r_sid == KNXIPFrame.CONNECT_RESPONSE:
            self.channel = received[6]
            logging.debug("Connected KNX IP tunnel (Channel: {})".format(self.channel,self.seq))
            # TODO: parse the other parts of the response
        else:
            raise Exception("Could not initiate tunnel connection, STI = {}".format(r_sid))
        


    def send_tunnelling_request(self, cemi):
        f = KNXIPFrame(KNXIPFrame.TUNNELING_REQUEST)
        b = bytearray([0x04,self.channel,self.seq,0x00]) # Connection header see KNXnet/IP 4.4.6 TUNNELLING_REQUEST
        if (self.seq < 0xff):
            self.seq += 1
        else:
            self.seq = 0

        b.extend(cemi.to_body())
        f.body=b

        self.data_server._sock.sendto(f.to_frame(), (self.remote_ip, self.remote_port))
        # TODO: wait for ack
        

    async def group_read(self, addr):
        """
        reads a value from the KNX bus

        Parameters
        ----------
        addr : number
            the group address to write to as an integer (0-65535)

        Returns
        -------
        res : int or bytes
            the value on the KNX bus

        Raises
        ------
        asyncio.TimeoutError
            when the KNX bus takes too long (0.1s and 0.5s) to answer the read request


        Notes
        -----
        This is still tricky, not all requests are answered

        """

        cemi = CEMIMessage()
        cemi.init_group_read(addr)

        self.read_queue.append(addr)
        self.send_tunnelling_request(cemi)
    
        # Wait for the result
        try:
            res = await asyncio.wait_for( self.result_queue.get(),0.1 )
        except:
            # Try one more time and raise a timeout exception on failure
            self.send_tunnelling_request(cemi)
            res = await asyncio.wait_for( self.result_queue.get(),0.5 )

        self.result_queue.task_done()

        return res
    
    def group_write(self, addr, data):
        """
        Writes a value to the knx bus

        Parameters
        ----------
        addr : number
            the group address to write to as an integer (0-65535)

        data : int or bytes
            the data to write to the KNX bus as integer or bytes

        Examples
        --------
        >>> import asyncio
        >>> import knxpy
        >>> async def main(loop):
        ...     tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
        ...     await tunnel.connect()
        ...     tunnel.group_write(2375,1)
        ...
        >>> loop = asyncio.get_event_loop()
        >>> loop.run_until_complete(main(loop))

        """

        cemi = CEMIMessage()
        cemi.init_group_write(addr, data)
        self.send_tunnelling_request(cemi)
    
            
    
class DataServerProtocol(object):
    """
    An UDP server protocol for recieving messages from the KNX ip gateway

    Examples
    --------
    >>> import asyncio
    >>> import socket

    >>> # get the local ip address
    >>> s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    >>> s.connect((remote_ip,remote_port))
    >>> local_ip=s.getsockname()[0]
    >>>
    >>> # get an event loop
    >>> loop = asyncio.get_event_loop()
    >>>
    >>> # start an UDP server
    >>> listen = loop.create_datagram_endpoint(DataServerProtocol, local_addr=(local_ip, 0))
    >>> transport, protocol = loop.run_until_complete(listen)
    >>>
    >>> # get the data port
    >>> data_port = transport._sock.getsockname()[1]
    >>>
    >>> # start the event loop
    >>> try:
    ...     loop.run_forever()
    ... except KeyboardInterrupt:
    ...     pass

    """

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        socket = self.transport._sock
        tunnel = self.transport.tunnel

        f = KNXIPFrame.from_frame(data)

        if f.service_type_id == KNXIPFrame.TUNNELING_REQUEST:
            req = KNXTunnelingRequest.from_body(f.body)
            msg = CEMIMessage.from_body(req.cEmi)
            send_ack = False
            
            if msg.code == 0x29:
                # LData.req
                send_ack = True
            elif msg.code == 0x2e:
                # LData.con
                send_ack = True
            else: 
                problem="Unimplemented cEMI message code {}".format(msg.code)
                logging.error(problem)
                raise Exception(problem)

            logging.debug("Received KNX message {}".format(msg))
            
            # Put RESPONSES into the result queue
            if (msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE and msg.dst_addr in tunnel.read_queue):
                # remove dst_addr from the read queue
                tunnel.read_queue.remove(msg.dst_addr)
                asyncio.get_event_loop().create_task( tunnel.result_queue.put(msg.data) )


            if send_ack:
                bodyack = bytearray([0x04, req.channel, req.seq, KNXIPFrame.E_NO_ERROR])
                ack = KNXIPFrame(KNXIPFrame.TUNNELLING_ACK)
                ack.body = bodyack
                socket.sendto(ack.to_frame(), addr)

