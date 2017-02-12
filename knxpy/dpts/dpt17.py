#!/usr/bin/env python3
"""
17.xxx
Scene Control

"""

def encode(value):
    return [0, int(value) & 0x3f]

def decode(data):
    if len(data) != 1:
        return None
    return struct.unpack('>B', data)[0] & 0x3f


