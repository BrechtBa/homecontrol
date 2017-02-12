#!/usr/bin/env python3
"""
24.xxx
???

"""

def encode(value):
    enc = bytearray(1)
    enc.extend(value.encode('iso-8859-1'))
    enc.append(0)
    return enc

def decode(data):
    return data.rstrip(b'\x00').decode('iso-8859-1')


