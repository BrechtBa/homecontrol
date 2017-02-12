#!/usr/bin/env python3
"""
20.xxx
Common HVAC Datapoint types

"""

def encode(value):
    return [0, int(value) & 0xff]

def decode(data):
    if len(data) != 1:
        return None
    return struct.unpack('>B', data)[0]


