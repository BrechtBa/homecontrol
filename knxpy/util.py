import struct
import logging

from enum import Enum

from knxpy import dpts

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MESSAGETYPE(Enum):
    KNXREAD = 0x00
    KNXWRITE = 0x80
    KNXRESPONSE = 0x40


def to_hex(ba):
    return "".join("%02x " % b for b in ba)


def str_to_bytes(s):
    return map(ord, s)


def bytes_to_str(b):
    return "".join(map(chr, b))


def ip_to_array(ipaddress):
    res = []
    for i in ipaddress.split("."):
        res.append(int(i))

    assert (len(res) == 4)
    return res


def int_to_array(i, length=2):
    res = []
    for _j in range(0, length):
        res.append(i & 0xff)
        i = i >> 8
    return reversed(res)


def encode_ga(str):
    parts = str.split('/')
    return (int(parts[0]) << 11) + (int(parts[1]) << 8) + int(parts[2])


def decode_ga(i):
    parts = [(i >> 11) & 0x1f, (i >> 8) & 0x07, i & 0xff]
    return '{}/{}/{}'.format(*parts)


def decode_pa(string):
    if len(string) != 2:
        return None
    pa = struct.unpack(">H", string)[0]
    return "{0}.{1}.{2}".format((pa >> 12) & 0x0f, (pa >> 8) & 0x0f, (pa) & 0xff)


def encode_dpt(data, dpt):
    if dpt in ['1', '1.001']:
        return dpts.dpt1.encode(data)
    elif dpt in ['2']:
        return dpts.dpt2.encode(data)
    elif dpt in ['3']:
        return dpts.dpt3.encode(data)
    elif dpt in ['4002', '4.002']:
        return dpts.dpt4002.encode(data)
    elif dpt in ['5']:
        return dpts.dpt5.encode(data)
    elif dpt in ['5001', '5.001']:
        return dpts.dpt5001.encode(data)
    elif dpt in ['6']:
        return dpts.dpt6.encode(data)
    elif dpt in ['7']:
        return dpts.dpt7.encode(data)
    elif dpt in ['8']:
        return dpts.dpt8.encode(data)
    elif dpt in ['9']:
        return dpts.dpt9.encode(data)
    elif dpt in ['10']:
        return dpts.dpt10.encode(data)
    elif dpt in ['11']:
        return dpts.dpt11.encode(data)
    elif dpt in ['12']:
        return dpts.dpt12.encode(data)
    elif dpt in ['13']:
        return dpts.dpt13.encode(data)
    elif dpt in ['14']:
        return dpts.dpt14.encode(data)
    elif dpt in ['16', '16000', '16.000']:
        return dpts.dpt16000.encode(data)
    elif dpt in ['16.001']:
        return dpts.dpt16001.encode(data)
    elif dpt in ['17']:
        return dpts.dpt17.encode(data)
    elif dpt in ['20']:
        return dpts.dpt20.encode(data)
    elif dpt in ['24']:
        return dpts.dpt24.encode(data)
    elif dpt in ['232']:
        return dpts.dpt232.encode(data)


def decode_dpt(data, dpt):
    if dpt in ['1', '1.001']:
        return dpts.dpt1.decode(data)
    elif dpt in ['2']:
        return dpts.dpt2.decode(data)
    elif dpt in ['3']:
        return dpts.dpt3.decode(data)
    elif dpt in ['4002', '4.002']:
        return dpts.dpt4002.decode(data)
    elif dpt in ['5']:
        return dpts.dpt5.decode(data)
    elif dpt in ['5001', '5.001']:
        return dpts.dpt5001.decode(data)
    elif dpt in ['6']:
        return dpts.dpt6.decode(data)
    elif dpt in ['7']:
        return dpts.dpt7.decode(data)
    elif dpt in ['8']:
        return dpts.dpt8.decode(data)
    elif dpt in ['9']:
        return dpts.dpt9.decode(data)
    elif dpt in ['10']:
        return dpts.dpt10.decode(data)
    elif dpt in ['11']:
        return dpts.dpt11.decode(data)
    elif dpt in ['12']:
        return dpts.dpt12.decode(data)
    elif dpt in ['13']:
        return dpts.dpt13.decode(data)
    elif dpt in ['14']:
        return dpts.dpt14.decode(data)
    elif dpt in ['16', '16000', '16.000']:
        return dpts.dpt16000.decode(data)
    elif dpt in ['16.001']:
        return dpts.dpt16001.decode(data)
    elif dpt in ['17']:
        return dpts.dpt17.decode(data)
    elif dpt in ['20']:
        return dpts.dpt20.decode(data)
    elif dpt in ['24']:
        return dpts.dpt24.decode(data)
    elif dpt in ['232']:
        return dpts.dpt232.decode(data)


class Message():
    def __init__(self, src, dst, flg, val):
        self.src = src
        self._dst = dst
        self.flg = flg
        self.val = val

    @property
    def dst(self):
        return decode_ga(self._dst)

    def __repr__(self):
        return '<message src: {src}, dst: {dst}, flg: {flg}, val: {val}>'.format(
            src=self.src, dst=self.dst, flg=self.flg, val=self.val)


def encode_data(fmt, data):
    """ encode the data using struct.pack
    >>> encoded = encode_data('HHB', (27, 1, 0))
    = ==================
    >   big endian
    H   unsigned integer
    B   unsigned char
    = ==================
    """
    ret = struct.pack('>' + fmt, *data)
    if len(ret) < 2 or len(ret) > 0xffff:
        raise ValueError('(encoded) data length needs to be between 2 and 65536')
    # prepend data length
    return struct.pack('>H', len(ret)) + ret


def decode_telegram(data):
    try:
        logger.debug('retrieved message {}'.format(' '.join(['{:02x}'.format(d) for d in data])))

        typ = struct.unpack(">H", data[0:2])[0]

        src = (data[4] << 8) | (data[5])
        dst = ((data[6]) << 8) | (data[7])
        flg = data[8] & 0xC0
        if len(data) == 10:
            val = data[9] & 0x3f
        else:
            val = data[10:]

        msg = Message(src, dst, flg, val)
        return msg
    except:
        logger.exception('could not decode message {}'.format(data))


def default_callback(message):
    print(message)
