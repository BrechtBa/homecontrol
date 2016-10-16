def tohex(ba):
    return "".join("%02x " % b for b in ba)

def str_to_bytes(s):
    return map(ord, s)

def bytes_to_str(b):
    return "".join(map(chr, b))

def ip_to_array(ipaddress):
    res=[]
    for i in ipaddress.split("."):
        res.append(int(i))
        
    assert(len(res)==4)
    return res

def int_to_array(i, length=2):
    res=[]
    for _j in range(0,length):
        res.append(i & 0xff)
        i = i >> 8
    return reversed(res)


def encode_ga(str):
    parts = str.split('/')

    return (int(parts[0]) << 11) + (int(parts[1]) << 8) + int(parts[2]) 


def decode_ga(i):
    parts = [(i >> 11) & 0x1f, (i >> 8) & 0x07, (i) & 0xff]

    return '{}/{}/{}'.format(*parts)

