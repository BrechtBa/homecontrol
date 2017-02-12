#!/usr/bin/env python3
"""
11.001
Date

"""

import datetime

def encode(date):
    return [0, date.day, date.month, date.year - 2000]



def decode(data):
    d = data[0] & 0x1f
    m = data[1] & 0x0f
    y = (data[2] & 0x7f) + 2000
    return datetime.date(y, m, d)


