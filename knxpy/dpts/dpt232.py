#!/usr/bin/env python3
"""
232
???

"""

import struct

def encode(value):
    return [0, int(value[0]) & 0xff, int(value[1]) & 0xff, int(value[2]) & 0xff]

def decode(data):
    if len(data) != 3:
        return None
    return list(struct.unpack('>BBB', data))


