import asyncio
import logging

import knxpy


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


async def main(loop):

    # connect
    tunnel = knxpy.KNXIPTunnel("192.168.1.3",3671,loop)
    await tunnel.connect()

    # read
    print('###   read    ###')
    v = await tunnel.group_read( knxpy.util.encode_ga('1/1/71') )
    print('read returned: {}'.format(v))
    
    # write
    await asyncio.sleep(0.5)
    print('###   write   ###')
    tunnel.group_write( knxpy.util.encode_ga('1/1/71'),1)

    # read
    print('###   read    ###')
    v = await tunnel.group_read( knxpy.util.encode_ga('1/1/71') )
    print('read returned: {}'.format(v))

    # write
    await asyncio.sleep(0.5)
    print('###   write   ###')
    tunnel.group_write( knxpy.util.encode_ga('1/1/71'),0)

    await asyncio.sleep(1.0)



loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))


