__author__ = 'code-museum'

from logbook import error, info

from hq.nice.zeromq import SafeClientZMQSocket, ZMQ_REQUEST, ZMQ_REPLY, SafeServerZMQSocket, zmq_poll, zmq_context


class Commander(object):
    COMMAND_TYPE_FIELD = 'command_type'
    PARAMETERS_FIELD = 'parameters'

    def __init__(self, commands_url):
        self._command_socket = SafeClientZMQSocket(zmq_context(), ZMQ_REQUEST, commands_url)

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
    STATUS_FIELD = u'status'
    VALUE_FIELD = u'value'

    def __init__(self, command_handling_url, socket_cls=SafeServerZMQSocket):
        self._command_handling_socket = socket_cls(zmq_context(), ZMQ_REPLY, command_handling_url)
        self._massage_type_to_handlers = {}

    def add_command_handler(self, command_type, handler):
        self._massage_type_to_handlers[command_type] = handler

    def add_safe_command_handler(self, command_type, handler):
        def safe_handler(*args, **kwargs):
            try:
                return True, handler(*args, **kwargs)
            except Exception as e:
                return False, e

        self._massage_type_to_handlers[command_type] = safe_handler

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

        if status is False and isinstance(value, Exception):
            self._command_handling_socket.send_json({self.STATUS_FIELD: status, self.VALUE_FIELD: str(value)})
            raise value
        self._command_handling_socket.send_json({self.STATUS_FIELD: status, self.VALUE_FIELD: value})
