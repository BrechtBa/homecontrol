#!/usr/bin/env python3
"""
5.xxx
8 Bit without Sign

"""

import struct


def encode(value):
    if value < 0:
        value = 0
    elif value > 255:
        value = 255
    return [0, int(value) & 0xff]


def decode(data):
    if len(data) != 1:
        return None
    return struct.unpack('>B', data)[0]


