#!/usr/bin/env python3
"""
9.xxx
2 Octet Floating Point Number

"""

import struct


def encode(value):
    s = 0
    e = 0
    if value < 0:
        s = 0x8000
    m = int(value * 100)
    while (m > 2047) or (m < -2048):
        e = e + 1
        m = m >> 1
    num = s | (e << 11) | (int(m) & 0x07ff)

    ret = bytearray([0])
    ret.extend(struct.pack('>H', int(num)))
    return ret


def decode(data):
    if len(data) != 2:
        return None
    i1 = data[0]
    i2 = data[1]
    s = (i1 & 0x80) >> 7
    e = (i1 & 0x78) >> 3
    m = (i1 & 0x07) << 8 | i2
    if s == 1:
        s = -1 << 11
    f = (m | s) * 0.01 * pow(2, e)
    return round(f, 2)


