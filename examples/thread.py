import logging
import time

import knxpy


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


tunnel = knxpy.ip.KNXIPTunnel("192.168.1.3",3671)
tunnel.connect()

# read dpt1
print('###   read    ###')
v = tunnel.group_read( '1/1/71' )
print('read returned: {}'.format(v))

# write dpt1
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( knxpy.util.encode_ga('1/1/71'),1)

# read dpt1
print('###   read    ###')
v = tunnel.group_read( knxpy.util.encode_ga('1/1/71') )
print('read returned: {}'.format(v))

# write dpt1
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( '1/1/71',0)

# read dpt9
time.sleep(0.5)
print('###   read    ###')
v = tunnel.group_read( '3/1/71', dpt='9')
print('read returned: {}'.format(v))

# write dpt5
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( '1/3/74',50, dpt='5')

# write dpt5
time.sleep(0.5)
print('###   write   ###')
tunnel.group_write( '1/3/74',255, dpt='5')
