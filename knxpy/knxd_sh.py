#!/usr/bin/env python3
#########################################################################
#  Copyright 2012-2013 Marcus Popp                         marcus@popp.mx
#########################################################################
#  This code was part of SmartHome.py.   http://mknx.github.io/smarthome/
#
#########################################################################


import logging
from threading import Thread
import struct
import binascii
import socket
import collections
import threading
import select
import time

from knxpy.util import default_callback, encode_ga, decode_pa, encode_dpt, Message


KNXREAD = 0x00
KNXRESP = 0x40
KNXWRITE = 0x80

logger = logging.getLogger(__name__)


class Base:
    _poller = None
    _family = {'UDP': socket.AF_INET, 'UDP6': socket.AF_INET6, 'TCP': socket.AF_INET, 'TCP6': socket.AF_INET6}
    _type = {'UDP': socket.SOCK_DGRAM, 'UDP6': socket.SOCK_DGRAM, 'TCP': socket.SOCK_STREAM, 'TCP6': socket.SOCK_STREAM}
    _monitor = []

    def __init__(self, monitor=False):
        self._name = self.__class__.__name__
        if monitor:
            self._monitor.append(self)

    def _create_socket(self, flags=None):
        family, type, proto, canonname, sockaddr = socket.getaddrinfo(self._host, self._port,
                                                                      family=self._family[self._proto],
                                                                      type=self._type[self._proto])[0]
        self.socket = socket.socket(family, type, proto)
        return sockaddr


class Connections(Base):

    _connections = {}
    _servers = {}
    _ro = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
    _rw = _ro | select.EPOLLOUT

    def __init__(self):
        Base.__init__(self)
        Base._poller = self
        self._epoll = select.epoll()

    def register_server(self, fileno, obj):
        self._servers[fileno] = obj
        self._connections[fileno] = obj
        self._epoll.register(fileno, self._ro)

    def register_connection(self, fileno, obj):
        self._connections[fileno] = obj
        self._epoll.register(fileno, self._ro)

    def unregister_connection(self, fileno):
        try:
            self._epoll.unregister(fileno)
            del(self._connections[fileno])
            del(self._servers[fileno])
        except:
            pass

    def monitor(self, obj):
        self._monitor.append(obj)

    def check(self):
        for obj in self._monitor:
            if not obj.connected:
                obj.connect()

    def trigger(self, fileno):
        if self._connections[fileno].outbuffer:
            self._epoll.modify(fileno, self._rw)

    def poll(self, callback=None):
        time.sleep(0.0000000001)  # give epoll.modify a chance
        if not self._connections:
            time.sleep(1)
            return
        for fileno in self._connections:
            if fileno not in self._servers:
                if self._connections[fileno].outbuffer:
                    self._epoll.modify(fileno, self._rw)
                else:
                    self._epoll.modify(fileno, self._ro)
        for fileno, event in self._epoll.poll(timeout=1):
            if fileno in self._servers:
                server = self._servers[fileno]
                server.handle_connection()
            else:
                if event & select.EPOLLIN:
                    try:
                        con = self._connections[fileno]
                        con._in(callback=callback)
                    except Exception as e:  # noqa
                        logger.exception(e)
                        con.close()
                        continue
                if event & select.EPOLLOUT:
                    try:
                        con = self._connections[fileno]
                        con._out()
                    except Exception as e:  # noqa
                        logger.exception(e)
                        con.close()
                        continue
                if event & (select.EPOLLHUP | select.EPOLLERR):
                    try:
                        con = self._connections[fileno]
                        con.close()
                        continue
                    except:
                        pass

    def close(self):
        for fileno in self._connections:
            try:
                self._connections[fileno].close()
            except:
                pass


class Stream(Base):

    def __init__(self, sock=None, address=None, monitor=False):
        Base.__init__(self, monitor=monitor)
        self.connected = False
        self.address = address
        self.inbuffer = bytearray()
        self.outbuffer = collections.deque()
        self._frame_size_in = 4096
        self._frame_size_out = 4096
        self.terminator = b'\r\n'
        self._balance_open = False
        self._balance_close = False
        self._close_after_send = False
        if sock is not None:
            self.socket = sock
            self._connected()

    def _connected(self):
            self._poller.register_connection(self.socket.fileno(), self)
            self.connected = True
            self.handle_connect()

    def _in(self, callback=None):
        max_size = self._frame_size_in
        try:
            data = self.socket.recv(max_size)
        except Exception as e:  # noqa
            logger.exception(e)
            self.close()
            return
        if data == b'':
            self.close()
            return
        self.inbuffer.extend(data)
        while True:
            terminator = self.terminator
            buffer_len = len(self.inbuffer)
            if not terminator:
                if not self._balance_open:
                    break
                index = self._is_balanced()
                if index:
                    data = self.inbuffer[:index]
                    self.inbuffer = self.inbuffer[index:]
                    self.found_balance(data)
                else:
                    break
            elif isinstance(terminator, int):
                if buffer_len < terminator:
                    break
                else:
                    data = self.inbuffer[:terminator]
                    self.inbuffer = self.inbuffer[terminator:]
                    self.terminator = 0
                    self.found_terminator(data, callback=callback)
            else:
                if terminator not in self.inbuffer:
                    break
                index = self.inbuffer.find(terminator)
                data = self.inbuffer[:index]
                cut = index + len(terminator)
                self.inbuffer = self.inbuffer[cut:]
                self.found_terminator(data, callback=callback)

    def _is_balanced(self):
        stack = []
        for index, char in enumerate(self.inbuffer):
            if char == self._balance_open:
                stack.append(char)
            elif char == self._balance_close:
                stack.append(char)
                if stack.count(self._balance_open) < stack.count(self._balance_close):
                    logger.warning("{}: unbalanced input!".format(self._name))
                    logger.close()
                    return False
                if stack.count(self._balance_open) == stack.count(self._balance_close):
                    return index + 1
        return False

    def _out(self):
        while self.outbuffer and self.connected:
            frame = self.outbuffer.pop()
            if not frame:
                if frame is None:
                    self.close()
                    return
                continue  # ignore empty frames
            try:
                sent = self.socket.send(frame)
            except socket.error:
                # logger.exception("{}: {}".format(self._name, e))
                self.outbuffer.append(frame)
                return
            else:
                if sent < len(frame):
                    self.outbuffer.append(frame[sent:])
        if self._close_after_send:
            self.close()

    def balance(self, bopen, bclose):
        self._balance_open = ord(bopen)
        self._balance_close = ord(bclose)

    def close(self):
        if self.connected:
            logger.debug("{}: closing socket {}".format(self._name, self.address))
        self.connected = False
        try:
            self._poller.unregister_connection(self.socket.fileno())
        except:
            pass
        try:
            self.handle_close()
        except:
            pass
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.socket.close()
        except:
            pass
        try:
            del self.socket
        except:
            pass

    def discard_buffers(self):
        self.inbuffer = bytearray()
        self.outbuffer.clear()

    def found_terminator(self, data, callback=None):
        pass

    def found_balance(self, data):
        pass

    def handle_close(self):
        pass

    def handle_connect(self):
        pass

    def send(self, data, close=False):
        self._close_after_send = close
        if not self.connected:
            return False
        frame_size = self._frame_size_out
        if len(data) > frame_size:
            for i in range(0, len(data), frame_size):
                self.outbuffer.appendleft(data[i:i + frame_size])
        else:
            self.outbuffer.appendleft(data)
        self._poller.trigger(self.socket.fileno())

        if not self.alive:
            # flush the out buffer if not running the listen loop
            self._out()
        return True


class Client(Stream):

    def __init__(self, host, port, proto='TCP', monitor=False):
        Stream.__init__(self, monitor=monitor)
        self._host = host
        self._port = port
        self._proto = proto
        self.address = "{}:{}".format(host, port)
        self._connection_attempts = 0
        self._connection_errorlog = 60
        self._connection_lock = threading.Lock()

    def connect(self):
        self._connection_lock.acquire()
        if self.connected:
            self._connection_lock.release()
            return
        try:
            sockaddr = self._create_socket()
            self.socket.settimeout(2)
            self.socket.connect(sockaddr)
            self.socket.setblocking(0)
            # self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception as e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                logger.error("could not connect to {} ({}): {}".format(self.address, self._proto, e))
                self._connection_attempts = self._connection_errorlog
            self.close()
        else:
            logger.debug("connected to {}".format(self.address))
            self._connected()
        finally:
            self._connection_lock.release()


class KNXD(Client):

    def __init__(self, ip='localhost', port=6720):
        super().__init__(ip, str(port), monitor=True)
        self.connections = Connections()

        self.gar = {}
        # self._init_ga = []
        # self._cache_ga = []
        self._lock = threading.Lock()
        # self._busmonitor = logger.debug
        self.found_terminator = None
        self.alive = None

    def _send(self, data):
        if len(data) < 2 or len(data) > 0xffff:
            logger.debug('illegal data size: {}'.format(repr(data)))
            return False
        # prepend data length
        send = bytearray(len(data).to_bytes(2, byteorder='big'))
        send.extend(data)
        self.send(send)

    def group_write(self, ga, data, dpt=None, flag='write'):
        pkt = bytearray([0, 39])
        if type(ga) is str:
            addr = encode_ga(ga)
        else:
            addr = ga
        if dpt is not None:
            data = encode_dpt(data, dpt)
        else:
            data = [data]

        pkt.extend(addr.to_bytes(2, byteorder='big'))
        pkt.extend([0])
        pkt.extend(data)

        if flag == 'write':
            flag = KNXWRITE
        elif flag == 'response':
            flag = KNXRESP
        else:
            logger.warning("groupwrite telegram for {0} with unknown flag: {1}. "
                           "Please choose beetween write and response.".format(ga, flag))
            return
        pkt[5] = flag | pkt[5]
        self._send(pkt)

    def group_read(self, ga):
        if type(ga) is str:
            addr = encode_ga(ga)
        else:
            addr = ga
        pkt = bytearray([0, 39])
        pkt.extend(addr.to_bytes(2, byteorder='big'))
        pkt.extend([0, KNXREAD])
        self._send(pkt)

    def handle_connect(self):
        self.discard_buffers()
        enable_cache = bytearray([0, 112])
        self._send(enable_cache)
        self.found_terminator = self.parse_length
        init = bytearray([0, 38, 0, 0, 0])
        self._send(init)
        self.terminator = 2

    def parse_length(self, length, callback=None):
        self.found_terminator = self.parse_telegram
        try:
            self.terminator = struct.unpack(">H", length)[0]
        except:
            logger.error("KNX: problem unpacking length: {0}".format(length))
            self.close()

    def parse_telegram(self, data, callback=None):
        self.found_terminator = self.parse_length  # reset parser and terminator
        self.terminator = 2
        # 2 byte type
        # 2 byte src
        # 2 byte dst
        # 2 byte command/data
        # x byte data
        typ = struct.unpack(">H", data[0:2])[0]
        if (typ != 39 and typ != 116) or len(data) < 8:
            # logger.debug("Ignore telegram.")
            return
        if data[6] & 0x03 or (data[7] & 0xC0) == 0xC0:
            logger.debug("Unknown APDU")
            return

        src = decode_pa(data[2:4])
        dst = struct.unpack(">H", data[4:6])[0]

        flg = data[7] & 0xC0
        if flg == KNXWRITE:
            flg = 'write'
        elif flg == KNXREAD:
            flg = 'read'
        elif flg == KNXRESP:
            flg = 'response'
        else:
            logger.warning("Unknown flag: {0:02x} src: {1} dest: {2}".format(flg, src, dst))
            return
        if len(data) == 8:
            val = data[7] & 0x3f
        else:
            val = data[8:]
        if flg == 'write' or flg == 'response':
            msg = Message(src, dst, flg, val)
            callback(msg)

        # elif flg == 'read':
        #     logger.debug("KNX: {0} read {1}".format(src, dst))
        #     if dst in self.gar:  # read item
        #         if self.gar[dst]['item'] is not None:
        #             item = self.gar[dst]['item']
        #             self.group_write(dst, item(), item.conf['knx_dpt'], 'response')
        #         if self.gar[dst]['logic'] is not None:
        #             self.gar[dst]['logic'].trigger('KNX', src, 'read', dst)

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        self.handle_close()

    def listen(self, callback=None):
        """
        Listen for messages on a knx server.
        """
        if callback is None:
            def callback(data):
                default_callback(data)

        def listen():
            self.run()
            while self.alive:
                try:
                    self.connections.poll(callback=callback)
                except Exception as e:
                    pass

        thread = Thread(target=listen)
        thread.start()
