#!/usr/bin/env python3
"""
Boolean data
1 bit
0,1
"""

def encode(value):
    return [int(value) & 0x01]


def decode(data):
    if len(data) != 1:
        return None
    return bool(data[0] & 0x01)

