#!/usr/bin/env python3
"""
7.xxx
2 Octet without Sign

"""

import struct

def encode(value):
    ret = bytearray([0])
    ret.extend(struct.pack('>H', int(value)))
    return ret


def decode(data):
    if len(data) != 2:
        return None
    return struct.unpack('>H', data)[0]


