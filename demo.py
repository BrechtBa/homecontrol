from knx.ip import KNXIPTunnel
import time
import logging

def main():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    tunnel = KNXIPTunnel("192.168.1.128",3671)
    tunnel.connect()
    
    while (True):
        # Toggle the value of group address 0/0/1
        tunnel.group_toggle(1)
        
        # display the values of group addresses 0/0/1 to 0/0/5
        for i in range(1,6):
            v=tunnel.group_read(i)
            print("{} = {}".format(i,v))

        # delay
        time.sleep(12)
        
if __name__ == '__main__':
    main()