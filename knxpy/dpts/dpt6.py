#!/usr/bin/env python3
"""
6.xxx
8 Bit with Sign

"""

import struct

def encode(value):
    if value < -128:
        value = -128
    elif value > 127:
        value = 127
    return [0, struct.pack('b', int(value))[0]]


def decode(data):
    if len(data) != 1:
        return None
    return struct.unpack('b', data)[0]


