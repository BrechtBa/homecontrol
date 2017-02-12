#!/usr/bin/env python3
"""
8.xxx
2 Octet with Sign

"""

import struct

def encode(value):
    if value < -32768:
        value = -32768
    elif value > 32767:
        value = 32767
    data = bytearray([0])
    data.extend(struct.pack('>h', int(value)))
    return data


def decode(data):
    if len(data) != 2:
        return None
    return struct.unpack('>h', data)[0]


