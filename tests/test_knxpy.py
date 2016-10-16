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



class TestKnxpy(unittest.TestCase):

    def test_version(self):
        self.assertGreater( len(knxpy.__version__), 0 )

    def test_iptunnel_connect(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))

    def test_iptunnel_write(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

            tunnel.group_write( knxpy.util.encode_ga('1/1/71'),1)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))

    def test_iptunnel_read_1(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

            tunnel.group_write( knxpy.util.encode_ga('1/1/71'),1)

            v = await tunnel.group_read( knxpy.util.encode_ga('1/1/71'))
            self.assertEqual( v, 1 )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))

    def test_iptunnel_read_0(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

            tunnel.group_write( knxpy.util.encode_ga('1/1/72'),0)

            v = await tunnel.group_read( knxpy.util.encode_ga('1/1/72'))
            self.assertEqual( v, 0 )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))


    def test_iptunnel_read_many(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

            for ga in ['1/1/71','1/1/72','1/1/73']:
                v = await tunnel.group_read( knxpy.util.encode_ga(ga))
                print(v)


        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))

    def test_iptunnel_read_float(self):
        async def main(loop):
   
            tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
            await tunnel.connect()

            v = await tunnel.group_read( knxpy.util.encode_ga('3/1/71'))
            print(v)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))

if __name__ == '__main__':
    unittest.main()
