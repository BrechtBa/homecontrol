from knx.ip import KNXIPTunnel
import time
import logging

def main():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    tunnel = KNXIPTunnel("192.168.1.128",3671)
    tunnel.connect()
    
    while (True):
        tunnel.group_toggle(1)
        time.sleep(1)
        for i in range(1,6):
            v=tunnel.group_read(i)
            print("{} = {}".format(i,v))
        time.sleep(120)
            


if __name__ == '__main__':
    main()