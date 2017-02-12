#!/usr/bin/env python3
"""
Character set
1 bit
0,1
"""

def encode(value):
    if isinstance(value, str):
        value = value.encode('iso-8859-1')
    else:
        value = str(value)
    return [0, ord(value) & 0xff]


def decode(data):
    if len(data) != 1:
        return None
    return payload.decode('iso-8859-1')

