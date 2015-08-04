__author__ = 'code-museum'

import zmq
from logbook import error, info

ZMQ_REQUEST = getattr(zmq, 'REQ')
ZMQ_REPLY = getattr(zmq, 'REP')
ZMQ_POLL_IN = getattr(zmq, 'POLLIN')


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
    COMMAND_TYPE_FIELD = 'command_type'
    PARAMETERS_FIELD = 'parameters'

    def __init__(self, commands_url):
        self._command_socket = SafeClientZMQSocket(zmq.Context(), ZMQ_REQUEST, commands_url)

    def command(self):
        pass

    def _command(self, command_type, **kwargs):
        command = {self.COMMAND_TYPE_FIELD: command_type, self.PARAMETERS_FIELD: kwargs}

        self._command_socket.send_json(command)
        if not zmq_poll(self._command_socket):
            error("Timeout while waiting for answer to command: %s" % command_type)
            self._command_socket.initialize()

        answer = self._command_socket.receive_json()
        if CommandsHandler.STATUS_FIELD not in answer or CommandsHandler.VALUE_FIELD not in answer:
            error("Answer format is wrong, use 'status' and 'value' attributes")
            return None
        if not answer[CommandsHandler.STATUS_FIELD]:
            error("Command not succeeded, because of %s" % answer['value'])
            return None
        return answer[CommandsHandler.VALUE_FIELD]


class CommandsHandler(object):
    STATUS_FIELD = 'status'
    VALUE_FIELD = 'value'

    def __init__(self, command_handling_url):
        self._command_handling_socket = SafeServerZMQSocket(zmq.Context(), ZMQ_REPLY, command_handling_url)
        self._massage_type_to_handlers = {}

    def add_command_handler(self, command_type, handler):
        self._massage_type_to_handlers[command_type] = handler

    def handle_commands(self):
        if not zmq_poll(self._command_handling_socket):
            error("Didn't get message")
            return

        msg = self._command_handling_socket.receive_json()

        if Commander.COMMAND_TYPE_FIELD not in msg:
            error("Massage invalid, please use 'type' attribute")
            (status, value) = False, 'got-bad-message'
        elif msg[Commander.COMMAND_TYPE_FIELD] not in self._massage_type_to_handlers:
            error("I don't know the type '%s', are you crazy?" % msg[Commander.COMMAND_TYPE_FIELD])
            (status, value) = False, 'got-bad-message-type'
        else:
            info("Got 'get-configuration' commands.")
            (status, value) = self._massage_type_to_handlers[
                msg[Commander.COMMAND_TYPE_FIELD]](**msg[Commander.PARAMETERS_FIELD])

        self._command_handling_socket.send_json({self.STATUS_FIELD: status, self.VALUE_FIELD: value})