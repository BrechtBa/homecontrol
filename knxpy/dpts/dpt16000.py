#!/usr/bin/env python3
"""
16.000
???

"""

def encode(value):
    enc = bytearray(1)
    enc.extend(value.encode('ascii')[:14])
    enc.extend([0] * (15 - len(enc)))
    return enc

def decode(data):
    return data.rstrip(b'0').decode()


