import socket
import threading

import logging
import socketserver
import queue
import time

from .core import KNXIPFrame,KNXTunnelingRequest,CEMIMessage
from . import util


class KNXIPTunnel():
    
    # TODO: implement a control server
    #    control_server = None
    data_server = None
    control_socket = None
    channel = 0
    seq = 0
    
    def __init__(self, ip, port, callback=None):
        self.remote_ip = ip
        self.remote_port = port
        self.discovery_port = None
        self.data_port = None
        self.result_dict = {}
        self.unack_queue = queue.Queue()
        self.callback = callback
        self.read_timeout = 0.1

    def connect(self):
        # Find my own IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.remote_ip,self.remote_port))
        local_ip=s.getsockname()[0]

        if self.data_server:
            logging.info("Data server already running, not starting again")
        else:
            self.data_server = DataServer((local_ip, 0), DataRequestHandler)
            self.data_server.tunnel = self 
            _ip, self.data_port = self.data_server.server_address
            data_server_thread = threading.Thread(target=self.data_server.serve_forever)
            data_server_thread.daemon = True
            data_server_thread.start()




        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_socket.bind((local_ip, 0))
        
        # Connect packet
        p=bytearray()
        p.extend([0x06,0x10]) # header size, protocol version
        p.extend(util.int_to_array(KNXIPFrame.CONNECT_REQUEST , 2))
        p.extend([0x00,0x1a]) # total length = 24 octet
        
        # Control endpoint
        p.extend([0x08,0x01]) # length 8 bytes, UPD
        _ip,port=self.control_socket.getsockname()
        p.extend(util.ip_to_array(local_ip))
        p.extend(util.int_to_array(port, 2)) 
        
        # Data endpoint
        p.extend([0x08,0x01]) # length 8 bytes, UPD
        p.extend(util.ip_to_array(local_ip))
        p.extend(util.int_to_array(self.data_port, 2)) 

        # 
        p.extend([0x04,0x04,0x02,0x00])

        self.control_socket.sendto(p, (self.remote_ip, self.remote_port))

        #TODO: non-blocking receive
        received = self.control_socket.recv(1024)
        received = bytearray(received)

        # Check if the response is an TUNNELING ACK
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
        self.data_server.socket.sendto(f.to_frame(), (self.remote_ip, self.remote_port))
        # TODO: wait for ack
        
        
    def group_read(self, ga, dpt=None):
        
        if type(ga) is str:
            addr = util.encode_ga(ga)
        else:
            addr = ga

        cemi = CEMIMessage()
        cemi.init_group_read(addr)
        self.send_tunnelling_request(cemi)

        # Wait for the result
        res = []
        starttime = time.time()
        runtime = 0
        while res == [] and runtime < self.read_timeout:
            if addr in self.result_dict:
                res = self.result_dict[addr]
                del self.result_dict[addr]
        

        if not dpt is None:
            res = util.decode_dpt(res,dpt)

        return res
    
    def group_write(self, ga, data, dpt=None):

        if type(ga) is str:
            addr = util.encode_ga(ga)
        else:
            addr = ga

        if not dpt is None:
            util.encode_dpt(data,dpt)

        cemi = CEMIMessage()
        cemi.init_group_write(addr, data)
        self.send_tunnelling_request(cemi)
    
    
    
class DataRequestHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        data = self.request[0]
        socket = self.request[1]
        
        f = KNXIPFrame.from_frame(data)
        
        if f.service_type_id == KNXIPFrame.TUNNELING_REQUEST:
            req = KNXTunnelingRequest.from_body(f.body)
            msg = CEMIMessage.from_body(req.cEmi)
            send_ack = False
            
            # print(msg)
            tunnel = self.server.tunnel
            
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
            print( '{} vs {}'.format(msg.cmd,CEMIMessage.CMD_GROUP_RESPONSE))
            if (msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE):
                tunnel.result_dict[msg.dst_addr] = msg.data

            # execute callback
            if not tunnel.callback is None:
                try:
                    tunnel.callback(msg)
                except exception as e:
                    logging.error("Error encountered durring callback execution: {}".format(e))


            if send_ack:
                bodyack = bytearray([0x04, req.channel, req.seq, KNXIPFrame.E_NO_ERROR])
                ack = KNXIPFrame(KNXIPFrame.TUNNELLING_ACK)
                ack.body = bodyack
                socket.sendto(ack.to_frame(), self.client_address)
            


 
class DataServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass
