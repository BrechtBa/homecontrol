import socket
import time
import logging
import asyncio


from knxpy.core import KNXIPFrame, KNXTunnelingRequest, CEMIMessage
from knxpy import util
from knxpy import ip


class KNXIPTunnel(ip.KNXIPTunnel):
    def __init__(self,ip,port,loop,callback=None):
        super().__init__(ip,port,callback=callback)

        self.loop = loop

    async def connect(self):
        """
        
        """
        # create the data server
        if self.data_server:
            logging.info("Data server already running, not starting again")
        else:
            listen = self.loop.create_datagram_endpoint(DataServerProtocol, local_addr=(self.local_ip, 0))
            transport, protocol = await listen
            transport.tunnel = self

            self.data_server = transport
            # get the data port
            self.data_port = transport.get_extra_info('sockname')[1]
            self.data_server.socket = self.data_server._sock

        # initiate tunneling
        self._initiate_tunneling()

    async def group_read(self, ga, dpt=None):
        """
        Reads a value from the KNX bus

        Parameters
        ----------
        ga : string or int
            the group address to write to as a string (e.g. '1/1/64') or an integer (0-65535)

        dpt : string
            the data point type of the group address, used to decode the result

        Returns
        -------
        res : 
            the decoded value on the KNX bus


        Notes
        -----
        This is still tricky, not all requests are answered and fast successive 
        read calls can lead to wrong answers

        """

        if type(ga) is str:
            addr = util.encode_ga(ga)
        else:
            addr = ga

        self.result_addr_dict[addr] = True

        cemi = CEMIMessage()
        cemi.init_group_read(addr)
        self.send_tunnelling_request(cemi)
    
        # Wait for the result
        res = None
        starttime = time.time()
        runtime = 0
        while res is None and runtime < self.read_timeout:
            if addr in self.result_dict:
                res = self.result_dict[addr]
                del self.result_dict[addr]
            await asyncio.sleep(0.01)
            runtime = time.time()-starttime

        del self.result_addr_dict[addr]

        if not res is None and not dpt is None:
            res = util.decode_dpt(res,dpt)

        return res


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
            
            # Put RESPONSES into the result dict
            if (msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE) and msg.dst_addr in tunnel.result_addr_dict:
                tunnel.result_dict[msg.dst_addr] = msg.data
                print(tunnel.result_dict)

            # execute callback
            if not tunnel.callback is None:
                try:
                    tunnel.loop.create_task(tunnel.callback(msg))
                except Exception as e:
                    logging.error("Error encountered durring callback execution: {}".format(e))

            if send_ack:
                bodyack = bytearray([0x04, req.channel, req.seq, KNXIPFrame.E_NO_ERROR])
                ack = KNXIPFrame(KNXIPFrame.TUNNELLING_ACK)
                ack.body = bodyack
                socket.sendto(ack.to_frame(), addr)

