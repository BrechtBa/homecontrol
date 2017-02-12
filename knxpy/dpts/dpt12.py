#!/usr/bin/env python3
"""
12.xxx
Octet without Sign

"""

import struct

def encode(value):
    if value < 0:
        value = 0
    elif value > 4294967295:
        value = 4294967295
    data = bytearray([0])
    data.extend(struct.pack('>I', int(value)))
    return data



def decode(data):
    if len(data) != 4:
        return None
    return struct.unpack('>I', data)[0]


