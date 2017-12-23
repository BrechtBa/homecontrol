#!/usr/bin/env python

import asyncio
import socket
import logging
import struct

from . import util

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

KNXWRITE = 0x80
KNXREAD = 0x00

EIB_GROUP_PACKET = 0x27
EIB_OPEN_GROUPCON = 0x26
    
    
class KNXD(object):

    def __init__(self, ip='localhost', port=6720, loop=None, callback=None):
        self.ip = ip
        self.port = port
        
        if callback is None:
            callback = default_callback
        self.callback = callback
        
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        
        self.read_timeout = 0.5

    async def connect(self):
        """
        Connect to a knxd server

        """

        self.socket = socket.socket()
        self.socket.connect((self.ip, int(self.port)))
        self.socket.send(encode_data('HHB', [EIB_OPEN_GROUPCON, 0, 0]))

        reader, writer = await asyncio.open_connection(self.ip, self.port)
        writer.write(encode_data('HHB', [EIB_OPEN_GROUPCON, 0, 0]))
        
        async def listen(reader):
            while True:
                data = await reader.read(100)
                self.callback(data)
        
        self.loop.create_task(listen(reader))
        
        #writer.close()


    async def group_read(self, ga):
        """
        Reads a value from the KNX bus

        Parameters
        ----------
        ga : string or int
            the group address to write to as a string (e.g. '1/1/64') or an integer (0-65535)

        """
        if type(ga) is str:
            addr = util.encode_ga(ga)
        else:
            addr = ga
        self.socket.send(encode_data('HHBB', [EIB_GROUP_PACKET, addr, 0, KNXREAD]))
        
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
            addr = util.encode_ga(ga)
        else:
            addr = ga
        if dpt is not None:
            util.encode_dpt(data,dpt)
        self.socket.send(encode_data('HHBB', [EIB_GROUP_PACKET, addr, 0, KNXWRITE | data]))

    def close(self):
        self.socket.close()


class message():
    def __init__(self, src, dst, flg, val):
        self.src = src
        self.dst = dst
        self.flg = flg
        self.val = val
        
    def __repr__(self):
        return 'src: {src}, dst: {dst}, flg: {flg}, val: {val}'.format(
            src=self.src, dst=util.decode_ga(self.dst), flg=self.flg, val=self.val)


def encode_data(fmt, data):
    """ encode the data using struct.pack
    >>> encoded = encode_data('HHB', (27, 1, 0))
    = ==================
    >   big endian
    H   unsigned integer
    B   unsigned char
    = ==================
    """
    ret = struct.pack('>' + fmt, *data)
    if len(ret) < 2 or len(ret) > 0xffff:
        raise ValueError('(encoded) data length needs to be between 2 and 65536')
    # prepend data length
    return struct.pack('>H', len(ret)) + ret
    
    
def default_callback(data):
    try:
        if len(data)>5: 
            typ = struct.unpack(">H", data[0:2])[0]
            src = (data[4] << 8) | (data[5])
            dst = ((data[6])<<8) | (data[7])
            flg = data[8] & 0xC0
            if len(data) == 10:
                val = data[9] & 0x3f
            else:
                val = data[10:]
            
            msg = message(src, dst, flg, val)
                
            return msg
    except:
        logger.exception('could not decode message {}'.format(data))

