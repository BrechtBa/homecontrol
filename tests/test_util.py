#!/usr/bin/env/ python
################################################################################
#    Copyright (c) 2016 Daniel Matuschek
#    This file is part of knxpy.
#    
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the "Software"), 
#    to deal in the Software without restriction, including without limitation 
#    the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#    and/or sell copies of the Software, and to permit persons to whom the 
#    Software is furnished to do so, subject to the following conditions:
#    
#    The above copyright notice and this permission notice shall be included in 
#    all copies or substantial portions of the Software.
################################################################################
import unittest
import asyncio

import knxpy



class TestUtil(unittest.TestCase):

    def test_encode_ga(self):
        self.assertEqual( knxpy.util.encode_ga('1/1/71'), 2375 )

    def test_decode_ga(self):
        self.assertEqual( knxpy.util.decode_ga(2375), '1/1/71' )

    def test_encode_dpt_1(self):
        self.assertEqual( knxpy.util.encode_dpt(0,'1'), [0] )

    def test_decode_dpt_1(self):
        self.assertEqual( knxpy.util.decode_dpt(1,'1'), 1 )

    def test_encode_dpt_5(self):
        self.assertEqual( knxpy.util.encode_dpt(140,'5'), [0,140] )

    def test_decode_dpt_5(self):
        self.assertEqual( knxpy.util.decode_dpt(b'\x8c','5'), 140 )

    def test_encode_dpt_9(self):
        self.assertEqual( knxpy.util.encode_dpt(22.64,'9'), b'\x00\x0cl' )

    def test_decode_dpt_9(self):
        self.assertEqual( knxpy.util.decode_dpt(b'\x0cl','9'), 22.64 )


if __name__ == '__main__':
    unittest.main()
