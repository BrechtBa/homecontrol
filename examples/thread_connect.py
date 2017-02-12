import knxpy

tunnel = knxpy.ip.KNXIPTunnel("192.168.1.3",3671)
tunnel.connect()

