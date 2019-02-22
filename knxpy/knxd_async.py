#!/usr/bin/env python

import asyncio
import socket
import logging

from knxpy.util import encode_ga, encode_dpt, encode_data, default_callback


logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


class KNXD(object):

    KNXWRITE = 0x80
    KNXREAD = 0x00

    EIB_GROUP_PACKET = 0x27
    EIB_OPEN_GROUPCON = 0x26

    def __init__(self, ip='localhost', port=6720, loop=None, callback=None, read_timeout=0.5):
        self.ip = ip
        self.port = port
        
        if callback is None:
            callback = default_callback
        self.callback = callback

        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

        self.read_timeout = read_timeout
        self.socket = None

    async def connect(self):
        """
        Connect to a knxd server

        """

        self.socket = socket.socket()
        self.socket.connect((self.ip, int(self.port)))
        self.socket.send(encode_data('HHB', [self.EIB_OPEN_GROUPCON, 0, 0]))

        reader, writer = await asyncio.open_connection(self.ip, self.port)
        writer.write(encode_data('HHB', [self.EIB_OPEN_GROUPCON, 0, 0]))
        
        async def listen(reader):
            while True:
                data = await reader.read(100)
                self.callback(data)
        
        self.loop.create_task(listen(reader))
        # writer.close()

    async def group_read(self, ga):
        """
        Reads a value from the KNX bus

        Parameters
        ----------
        ga : string or int
            the group address to write to as a string (e.g. '1/1/64') or an integer (0-65535)

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
            the group address to write to as a string (e.g. '1/1/64') or an integer (0-65535)

        dpt : string
            the data point type of the group address, used to encode the data

        """

        if type(ga) is str:
            addr = encode_ga(ga)
        else:
            addr = ga
        if dpt is not None:
            encode_dpt(data, dpt)
        self.socket.send(encode_data('HHBB', [self.EIB_GROUP_PACKET, addr, 0, self.KNXWRITE | data]))

    def close(self):
        self.socket.close()
