#!/usr/bin/env python3
"""
5.001
8 Bit without Sign

"""

import struct


def encode(value):
    if value < 0:
        value = 0
    elif value > 100:
        value = 100
    return [0, int(value * 255.0 / 100) & 0xff]


def decode(data):
    if len(data) != 1:
        return None
    return struct.unpack('>B', data)[0] * 100.0 / 255


