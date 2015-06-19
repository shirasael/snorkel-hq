__author__ = 'code-museum'

import zmq

ZMQ_REQUEST = zmq.REQ
ZMQ_REPLY = zmq.REP
ZMQ_POLL_IN = zmq.POLLIN

def zmq_poll(socket, timeout=3000):
    return socket.poll(timeout) == ZMQ_POLL_IN


class ClientZMQSocket(object):
    def __init__(self, context, socket_type, address):
        self._context = context
        self._socket_type = socket_type
        self._address = address
        self._socket = None

    def _initialize(self):
        self._socket = self._context.socket(self._socket_type)
        self._socket.connect(self._address)

    @property
    def socket(self):
        if not self._socket:
            self._initialize()
        return self._socket


class ServerZMQSocket(object):
    def __init__(self, context, socket_type, address):
        self._context = context
        self._socket_type = socket_type
        self._address = address
        self._socket = None

    def _initialize(self):
        self._socket = self._context.socket(self._socket_type)
        self._socket.bind(self._address)

    @property
    def socket(self):
        if not self._socket:
            self._initialize()
        return self._socket
