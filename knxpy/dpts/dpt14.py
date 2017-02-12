#!/usr/bin/env python3
"""
14.xxx
Octet Floating Point Number

"""

import struct

def encode(value):
    data = bytearray([0])
    data.extend(struct.pack('>f', int(value)))
    return data



def decode(data):
    if len(data) != 4:
        return None
    return struct.unpack('>f', data)[0]


