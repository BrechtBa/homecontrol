#!/usr/bin/env python3
"""
13.xxx
Octet with Sign

"""

import struct

def encode(value):
    if value < -2147483648:
        value = -2147483648
    elif value > 2147483647:
        value = 2147483647
    data = bytearray([0])
    data.extend(struct.pack('>i', int(value)))
    return data



def decode(data):
    if len(data) != 4:
        return None
    return struct.unpack('>i', data)[0]


