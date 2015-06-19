__author__ = 'code-museum'

import zmq
from logbook import error

ZMQ_REQUEST = zmq.REQ
ZMQ_REPLY = zmq.REP
ZMQ_POLL_IN = zmq.POLLIN

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


class Commander(object):
    STATUS_FIELD = 'status'
    VALUE_FIELD = 'value'

    def __init__(self, commands_url):
        self._command_socket = SafeClientZMQSocket(zmq.Context(), ZMQ_REQUEST, commands_url)

    def command(self, command_type, **values):
        command = {'type': command_type}
        if values:
            command.update(values)

        self._command_socket.send_json(command)
        if not zmq_poll(self._command_socket):
            error("Timeout while waiting for answer to command: %s" % command_type)
            self._command_socket.initialize()

        answer = self._command_socket.receive_json()
        if self.STATUS_FIELD not in answer or self.VALUE_FIELD not in answer:
            error("Answer format is wrong, use 'success' and 'value' attributes")
            return None
        if not answer['success']:
            error("Command not succeeded, because of %s" % answer['value'])
            return None
        return answer['value']