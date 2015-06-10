from logbook import info
from _hq.consts import GET_ALL_SYSTEMS_COMMAND, PUT_CONFIGURATION_COMMAND

__author__ = 'code-museum'

from datetime import datetime, timedelta

from _hq import consts

import zmq


class SnorkelHQCommander(object):
    def __init__(self, hq_server_name, command_queue_url='tcp://%s:12346'):
        self._command_queue_url = command_queue_url
        self._command_queue = None
        self._hq_server = hq_server_name
        self._initialized = False

    def initialize(self):
        ctx = zmq.Context()
        self._command_queue = ctx.socket(zmq.REQ)
        self._command_queue.connect(self._command_queue_url % self._hq_server)
        self._initialized = True

    def _force_initialize(self):
        if not self._initialized:
            raise Exception("Please initialize this class with initialize() function!")

    def get_all_systems(self):
        self._force_initialize()
        return self.command(GET_ALL_SYSTEMS_COMMAND)

    def get_all_configurations(self, system):
        self._force_initialize()
        return self.command(GET_ALL_SYSTEMS_COMMAND, value=system)

    def deploy_configuration(self, server, system, file_name, config):
        self._force_initialize()
        return self.command(PUT_CONFIGURATION_COMMAND, value={'server': server, 'system': system, 'file_name': file_name, 'config': config})

    def command(self, type, value=None):
        self._command_queue.send_json({'type': type, 'value': value})
        if self._command_queue.poll(3000) != zmq.POLLIN:
            self._initialized = False
            raise Exception('Timeout after not getting answer for command %s' % type)
        return self._command_queue.recv_json()


class AgentCore(object):
    def _get_systems(self):
        raise NotImplementedError()

    def _get_configurations(self, system):
        raise NotImplementedError()

    def _get_configuration(self, system, configuration_id):
        raise NotImplementedError()

    def _put_configuration(self, system, configuration_id, configuration_content):
        raise NotImplementedError()

    def systems(self):
        return self._get_systems()

    def get_all_configurations(self, system):
        return self._get_configurations(system)

    def get_configuration(self, system, configuration_id):
        return self._get_configuration(system, configuration_id)

    def put_configuration(self, system, configuration_id, configuration_content):
        return self._put_configuration(system, configuration_id, configuration_content)


class SnorkelAgent(object):
    def __init__(self, client_core, hq_server_name, registration_queue_url='tcp://localhost:12345'):
        self._registration_queue_url = registration_queue_url
        self._registration_queue = None
        self._command_queue = None
        self._client_core = client_core
        self._hq_server_name = hq_server_name
        self._command_queue_address = ''

    def initialize(self):
        ctx = zmq.Context()
        self._registration_queue = ctx.socket(zmq.REQ)
        self._registration_queue.connect(self._registration_queue_url)
        self._command_queue = ctx.socket(zmq.REP)
        port = self._command_queue.bind_to_random_port('tcp://*')
        self._command_queue_address = 'tcp://%s:%s' % (self._hq_server_name, port)

    def say_hi(self):
        info(self._command_queue_address)
        self._registration_queue.send_json({'type': consts.GREETING_TYPE,
                                            'server': self._hq_server_name,
                                            'command_queue_address': self._command_queue_address})
        self._registration_queue.recv_json()

    def handle_command_request(self):
        if self._command_queue.poll(3000) != zmq.POLLIN:
            print "Didn't get message"
            return

        msg = self._command_queue.recv_json()
        if msg['type'] == consts.GET_SYSTEM_TYPE:
            (success, value) = self._client_core.systems()
            print value
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.GET_ALL_CONFIGURATIONS_MESSAGE:
            (success, value) = self._client_core.get_all_configurations(msg['system'])
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.GET_CONFIGURATION_COMMAND:
            (success, value) = self._client_core.get_configuration(msg['system'], msg['configuration_id'])
            self._command_queue.send_json({'success': success, 'value': value})
        elif msg['type'] == consts.PUT_CONFIGURATION_COMMAND:
            (success, value) = self._client_core.put_configuration(msg['system'], msg['configuration_id'],
                                                                   msg['configuration_content'])
            self._command_queue.send_json({'success': success, 'value': value})
        else:
            self._command_queue.send_json('BAD_TYPE')


class SnorkelAgentRunner(object):
    def __init__(self, agent):
        self._agnet = agent

    def start(self):
        last_time_welcoming = None
        self._agnet.initialize()
        while True:
            if not last_time_welcoming or last_time_welcoming <= datetime.now() - timedelta(seconds=15):
                self._agnet.say_hi()
                last_time_welcoming = datetime.now()
            self._agnet.handle_command_request()
