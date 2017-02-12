#!/usr/bin/env python3
"""
10.001
Time

"""

import datetime

def encode(dt):
    return [0, (dt.isoweekday() << 5) | dt.hour, dt.minute, dt.second]


def decode(data):
    h = data[0] & 0x1f
    m = data[1] & 0x3f
    s = data[2] & 0x3f
    return datetime.time(h, m, s)


