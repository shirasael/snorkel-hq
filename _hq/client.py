__author__ = 'code-museum'

from _hq import consts

import zmq


class AgentClientCore(object):
    def __init__(self, server_name, get_system_callback, get_all_configuration_callback, get_configuration_callback,
                 put_configuration_callback):
        self.server_name = server_name
        self._get_system_callback = get_system_callback
        self._get_all_configuration_callback = get_all_configuration_callback
        self._get_configuration_callback = get_configuration_callback
        self._put_configuration_callback = put_configuration_callback

    def systems(self):
        return self._get_system_callback.__call__()

    def get_all_configurations(self, system):
        return self._get_all_configuration_callback.__call__()

    def get_configuration(self, system, configuration_id):
        return self._get_configuration_callback.__call__(system, configuration_id)

    def put_configuration(self, system, configuration_id, configuration_content):
        return self._put_configuration_callback.__call__(system, configuration_id, configuration_content)


class AgentClient(object):
    def __init__(self, client_core, hq_server):
        self._registration_queue = None
        self._command_queue = None
        self._client_core = client_core
        self._hq_server = hq_server
        self._command_queue_address = ''

    def initialize(self):
        ctx = zmq.Context()
        self._registration_queue = ctx.socket(zmq.REQ)
        self._registration_queue.connect('tcp://%s:12345' % self._hq_server)
        self._command_queue = ctx.socket(zmq.REP)
        port = self._command_queue.bind_to_random_port('tcp://*')
        self._command_queue_address = 'tcp://%s:%s' % (self._client_core.server_name, port)

    def say_hi(self):
        self._registration_queue.send_json({'type': consts.GREETING_TYPE,
                                            'server': self._client_core.server_name,
                                            'command_queue_address': self._command_queue_address})
        self._registration_queue.recv_json()

    def handle_command_request(self):
        if self._command_queue.poll(3000) != zmq.POLLIN:
            print "Didn't get message"
            return

        msg = self._command_queue.recv_json()
        if msg['type'] == consts.GET_SYSTEM_TYPE:
            (success, value) = self._client_core.system()
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.GET_SYSTEM_TYPE:
            (success, value) = self._client_core.get_all_configurations(msg['system'])
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.GET_CONFIGURATION_TYPE:
            (success, value) = self._client_core.get_configuration(msg['system'], msg['configuration_id'])
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.GET_CONFIGURATION_TYPE:
            (success, value) = self._client_core.put_configuration(msg['system'], msg['configuration_id'],
                                                                   msg['configuration_content'])
            self._command_queue.send_json({'success': success, 'value': value})
        else:
            self._command_queue.send_json('BAD_TYPE')
