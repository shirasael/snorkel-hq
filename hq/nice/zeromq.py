__author__ = 'code-museum'

import zmq

ZMQ_REQUEST = getattr(zmq, 'REQ')
ZMQ_REPLY = getattr(zmq, 'REP')
ZMQ_POLL_IN = getattr(zmq, 'POLLIN')


def zmq_context(io_threads=1, **kwargs):
    return zmq.Context(io_threads, **kwargs)


def zmq_poll(socket, timeout=3000):
    return socket.poll(timeout) == ZMQ_POLL_IN


class SafeZMQSocket(object):
    def __init__(self, context, socket_type, address):
        self._context = context
        self._socket_type = socket_type
        self._address = address
        self._socket = None

    def _initialize(self):
        raise NotImplementedError

    def initialize(self):
        self._initialize()

    @property
    def _initialized_socket(self):
        if not self._socket:
            self._initialize()
        return self._socket

    def receive_json(self):
        return self._initialized_socket.recv_json()

    def send_json(self, value):
        self._initialized_socket.send_json(value)

    def poll(self, timeout):
        return self._initialized_socket.poll(timeout)


class SafeClientZMQSocket(SafeZMQSocket):
    def _initialize(self):
        self._socket = self._context.socket(self._socket_type)
        self._socket.connect(self._address)


class SafeServerZMQSocket(SafeZMQSocket):
    def _initialize(self):
        self._socket = self._context.socket(self._socket_type)
        self._socket.bind(self._address)


class SafeRandomPortServerZMQSocket(SafeZMQSocket):
    def _initialize(self):
        self._socket = self._context.socket(self._socket_type)
        self._port = self._socket.bind_to_random_port(self._address)

    def socket_client_url(self, hostname):
        if not self._socket:
            self._initialize()
        return 'tcp://%s:%s' % (hostname, self._port)
