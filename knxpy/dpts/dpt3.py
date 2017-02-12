#!/usr/bin/env python3
"""
Bit with control
4 bit
0-255
"""


def encode(value):
    return [(int(value[0]) << 3) & 0x08 | int(value[1]) & 0x07]


def decode(data):
    if len(data) != 1:
        return None
    return [data[0] >> 3 & 0x01, data[0] & 0x07]

