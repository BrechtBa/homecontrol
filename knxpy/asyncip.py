import socket
import asyncio

import logging

from .core import KNXIPFrame,KNXTunnelingRequest,CEMIMessage
from . import util


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
        s.close()

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
        
        # close the control socket
        control_socket.close()
        

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
            when the KNX bus takes too long (0.1s and 0.5s) to answer the read 
            request


        Notes
        -----
        This is still tricky, not all requests are answered and fast successive 
        read calls can lead to wrong answers

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

