#!/usr/bin/env python3
"""

???

"""

def encode(value):
    # control, value
    return [(value[0] << 1) & 0x02 | value[1] & 0x01]


def decode(data):
    if len(data) != 1:
        return None
    return [data[0] >> 1 & 0x01, data[0] & 0x01]

