#!/usr/bin/env python3
"""
16.001
???

"""

def encode(value):
    enc = bytearray(1)
    enc.extend(value.encode('iso-8859-1')[:14])
    enc.extend([0] * (15 - len(enc)))
    return enc

def decode(data):
    return payload.rstrip(b'0').decode('iso-8859-1')


