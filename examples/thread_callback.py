import time
import knxpy
import __main__


def callback(msg):
    print('ga: {}'.format( knxpy.util.decode_ga(msg.dst_addr) ))
    print('data: {}'.format(msg.data))
    print('')

tunnel = knxpy.ip.KNXIPTunnel("192.168.1.3",3671,callback=callback)
tunnel.connect()


print('Make changes on the KNX bus some other way and see the result')
print('Sleep for 30 seconds')
time.sleep(30)

