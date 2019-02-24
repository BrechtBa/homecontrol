#!/usr/bin/env python
import time
import socket
import logging
from threading import Thread

from knxpy.util import encode_ga, encode_dpt, encode_data, default_callback


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KNXD(object):

    KNXWRITE = 0x80
    KNXREAD = 0x00

    EIB_GROUP_PACKET = 0x27
    EIB_OPEN_GROUPCON = 0x26

    def __init__(self, ip='localhost', port=6720, read_timeout=0.5):
        self.ip = ip
        self.port = port

        self.read_timeout = read_timeout
        self.socket = None
        self.connected = False
        self.listening = False

    def connect(self):
        """
        Connect to a knxd server, after connection commands can be sent.
        """

        self.socket = socket.socket()
        self.socket.connect((self.ip, int(self.port)))
        self.socket.send(encode_data('HHB', [self.EIB_OPEN_GROUPCON, 0, 0]))
        self.connected = True

    def listen(self, callback=None):
        """
        Listen for messages on a knx server.
        """
        if callback is None:
            def callback(data):
                print(default_callback(data))

        def listen():
            self.listening = True
            while self.listening:
                logger.debug('opening new connection')
                recv_socket = socket.socket()
                recv_socket.connect((self.ip, int(self.port)))
                recv_socket.send(encode_data('HHB', [self.EIB_OPEN_GROUPCON, 0, 0]))

                while self.listening:
                    try:
                        data = recv_socket.recv(1024)
                        callback(data)
                    except:
                        logger.exception('exception while listening')
                        break
                recv_socket.close()
                time.sleep(1)

        thread = Thread(target=listen)
        thread.start()

    def group_read(self, ga):
        """
        Reads a value from the KNX bus

        Parameters
        ----------
        ga : string or int
            The group address to write to as a string (e.g. '1/1/64') or an integer (0-65535).

        """
        if type(ga) is str:
            addr = encode_ga(ga)
        else:
            addr = ga

        self.socket.send(encode_data('HHBB', [self.EIB_GROUP_PACKET, addr, 0, self.KNXREAD]))
        
    def group_write(self, ga, data, dpt=None):
        """
        Writes a value to the KNX bus

        Parameters
        ----------
        ga : string or int
            The group address to write to as a string (e.g. '1/1/64') or an integer (0-65535).
        dpt : string
            The data point type of the group address, used to encode the data.

        """
        if type(ga) is str:
            addr = encode_ga(ga)
        else:
            addr = ga
        if dpt is not None:
            encode_dpt(data, dpt)

        self.socket.send(encode_data('HHBB', [self.EIB_GROUP_PACKET, addr, 0, self.KNXWRITE | data]))

    def close(self):
        self.connected = False
        self.listening = False
        self.socket.close()
