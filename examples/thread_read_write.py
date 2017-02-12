import logging
import time

import knxpy


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


tunnel = knxpy.ip.KNXIPTunnel("192.168.1.3",3671)
tunnel.connect()

# read
print('###   read    ###')
v = tunnel.group_read( knxpy.util.encode_ga('1/1/71') )
print('read returned: {}'.format(v))

# write
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( knxpy.util.encode_ga('1/1/71'),1)

# read
print('###   read    ###')
v = tunnel.group_read( knxpy.util.encode_ga('1/1/71') )
print('read returned: {}'.format(v))

# write
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( knxpy.util.encode_ga('1/1/71'),0)


