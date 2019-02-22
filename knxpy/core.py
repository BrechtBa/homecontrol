from . import util


class KNXIPFrame:
    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0111
    TUNNELING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531

    DEVICE_MGMT_CONNECTION = 0x03
    TUNNEL_CONNECTION = 0x04
    REMLOG_CONNECTION = 0x06
    REMCONF_CONNECTION = 0x07
    OBJSVR_CONNECTION = 0x08

    E_NO_ERROR = 0x00
    E_HOST_PROTOCOL_TYPE = 0x01
    E_VERSION_NOT_SUPPORTED = 0x02
    E_SEQUENCE_NUMBER = 0x04
    E_CONNECTION_ID = 0x21
    E_CONNECTION_TYPE = 0x22
    E_CONNECTION_OPTION = 0x23
    E_NO_MORE_CONNECTIONS = 0x24
    E_DATA_CONNECTION = 0x26
    E_KNX_CONNECTION = 0x27
    E_TUNNELING_LAYER = 0x28

    body = None

    def __init__(self, service_type_id):
        self.service_type_id = service_type_id

    def to_frame(self):
        return self.header() + self.body

    @classmethod
    def from_frame(cls, frame):
        # TODO: Check length
        p = cls(frame[2] * 256 + frame[3])
        p.body = frame[6:]
        return p

    def total_length(self):
        return 6 + len(self.body)

    def header(self):
        tl = self.total_length()
        res = bytearray([0x06, 0x10, 0, 0, 0, 0])
        res[2] = (self.service_type_id >> 8) & 0xff
        res[3] = (self.service_type_id >> 0) & 0xff
        res[4] = (tl >> 8) & 0xff
        res[5] = (tl >> 0) & 0xff
        return res


class KNXTunnelingRequest:
    seq = 0
    cEmi = None
    channel = 0

    def __init__(self):
        pass

    @classmethod
    def from_body(cls, body):
        # TODO: Check length
        p = cls()
        p.channel = body[1]
        p.seq = body[2]
        p.cEmi = body[4:]
        return p

    def __str__(self):
        return ""


class CEMIMessage():
    CMD_GROUP_READ = 1
    CMD_GROUP_WRITE = 2
    CMD_GROUP_RESPONSE = 3
    CMD_UNKNOWN = 0xff

    code = 0
    ctl1 = 0
    ctl2 = 0
    src_addr = None
    dst_addr = None
    cmd = None
    tpci_apci = 0
    mpdu_len = 0
    data = [0]

    def __init__(self):
        pass

    @classmethod
    def from_body(cls, cemi):

        # TODO: check that length matches
        m = cls()
        m.code = cemi[0]
        offset = cemi[1]

        m.ctl1 = cemi[2 + offset]
        m.ctl2 = cemi[3 + offset]

        m.src_addr = cemi[4 + offset] * 256 + cemi[5 + offset]
        m.dst_addr = cemi[6 + offset] * 256 + cemi[7 + offset]

        m.mpdu_len = cemi[8 + offset]

        tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = tpci_apci & 0x3ff

        # for APCI codes see KNX Standard 03/03/07 Application layer 
        # table Application Layer control field
        if (apci & 0x080):
            # Group write
            m.cmd = CEMIMessage.CMD_GROUP_WRITE
        elif (apci == 0):
            m.cmd = CEMIMessage.CMD_GROUP_READ
        elif (apci & 0x40):
            m.cmd = CEMIMessage.CMD_GROUP_RESPONSE
        else:
            m.cmd = CEMIMessage.CMD_NOT_IMPLEMENTED

        apdu = cemi[10 + offset:]
        if len(apdu) != m.mpdu_len:
            raise Exception("APDU LEN should be {} but is {}".format(m.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            m.data = apci & 0x2f
        else:
            m.data = cemi[11 + offset:]

        return m

    def init_group(self, dst_addr=1):
        self.code = 0x11  # Comes from packet dump, why?
        self.ctl1 = 0xbc  # frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0, confirm-flag 0
        self.ctl2 = 0xe0  # dst addr type 1, hop count 6, extended frame format
        self.src_addr = 0
        self.dst_addr = dst_addr

    def init_group_write(self, dst_addr=1, data=0):
        self.init_group(dst_addr)
        self.tpci_apci = 0x00 * 256 + 0x80  # unnumbered data packet, group write
        self.data = data

    def init_group_read(self, dst_addr=1):
        self.init_group(dst_addr)
        self.tpci_apci = 0x00  # unnumbered data packet, group read
        self.data = 0

    def to_body(self):
        b = [
            self.code,
            0x00,
            self.ctl1,
            self.ctl2,
            (self.src_addr >> 8) & 0xff,
            (self.src_addr >> 0) & 0xff,
            (self.dst_addr >> 8) & 0xff,
            (self.dst_addr >> 0) & 0xff,
        ]

        if type(self.data) == list:
            data = self.data
        else:
            data = [self.data]

        if len(data) == 1:
            if (data[0] & 3) == data[0]:
                # dpt1 data is added to the acpi byte and not data bytes are added
                b.extend([1, (self.tpci_apci >> 8) & 0xff, ((self.tpci_apci >> 0) & 0xff) + data[0]])
            else:
                b.extend([1 + len(data), (self.tpci_apci >> 8) & 0xff, (self.tpci_apci >> 0) & 0xff])
                b.extend(data)
        else:
            if (data[0] & 3) == data[0] and data[1] == 0:
                # dpt1 data is added to the acpi byte and not data bytes are added
                b.extend([1, (self.tpci_apci >> 8) & 0xff, ((self.tpci_apci >> 0) & 0xff) + data[0]])
            else:
                b.extend([len(data), (self.tpci_apci >> 8) & 0xff, ((self.tpci_apci >> 0) & 0xff) + data[0]])
                b.extend(data[1:])

        return b

    def __str__(self):

        c = "??"
        if self.cmd == self.CMD_GROUP_READ:
            c = "read"
        elif self.cmd == self.CMD_GROUP_WRITE:
            c = "write"
        elif self.cmd == self.CMD_GROUP_RESPONSE:
            c = "response"
        return "{0:<10}-> {1:<10} {2} {3}".format(util.decode_ga(self.src_addr), util.decode_ga(self.dst_addr), c,
                                                  self.data)
