__author__ = 'code-museum'

import zmq
from logbook import info, error

from hq.nice import ZMQ_REQUEST, ZMQ_REPLY, ZMQ_POLL_IN, zmq_poll


class AgentCommander(object):
    def __init__(self, address, hostname):
        self._address = address
        self._hostname = hostname
        self._command_queue = None

    def initialize(self):
        ctx = zmq.Context()
        self._command_queue = ctx.socket(ZMQ_REQUEST)
        self._command_queue.connect(self._address)

    def command(self, type, **values):
        command = {'type': type}
        if values:
            command.update(values)

        self._command_queue.send_json(command)
        if self._command_queue.poll(3000) != ZMQ_POLL_IN:
            error("Timeout while waiting for answer to command: %s" % type)
            self.initialize()
        answer = self._command_queue.recv_json()
        if 'success' not in answer or 'value' not in answer:
            error("Answer format is wrong, use 'success' and 'value' attributes")
            return None
        if not answer['success']:
            error("Command not succeeded, because of %s" % answer['value'])
            return None
        return answer

    def get_systems(self):
        answer = self.command(SnorkelAgent.GET_SYSTEMS)
        if not answer:
            return []

        info("Got systems %s from agent" % answer['value'])
        return answer['value']

    def get_configurations(self, system_id):
        answer = self.command(SnorkelAgent.GET_CONFIGURATIONS, system_id=system_id)
        if not answer:
            return []

        info("Got all configurations: %s from agent" % answer['value'])
        return answer['value']

    def load_configuration(self, system_id, configuration_id):
        answer = self.command(SnorkelAgent.LOAD_CONFIGURATION, system_id=system_id, configuration_id=configuration_id)
        if not answer:
            return []

        info("Load configuration: %s from agent" % answer['value'])
        return answer['value']

    def update_configuration(self, system_id, configuration_id, configuration_content):
        answer = self.command(SnorkelAgent.LOAD_CONFIGURATION, system_id=system_id, configuration_id=configuration_id,
                              configuration_content=configuration_content)
        if not answer:
            return

        info('Configuration update succeed')


class SnorkelAgent(object):
    GREETING_MSG = 'hello-you'
    GET_SYSTEMS = 'get-systems'
    GET_CONFIGURATIONS = 'get-configurations'
    LOAD_CONFIGURATION = 'load-configuration'
    PUT_CONFIGURATION = 'put-configuration'

    def __init__(self, client_core, agent_hostname, registration_queue_url='tcp://localhost:12345'):
        assert isinstance(client_core, AgentCore)
        self._agent_client_core = client_core
        self._agent_hostname = agent_hostname
        self._registration_queue_url = registration_queue_url

        self._registration_queue = None
        self._command_queue = None
        self._command_queue_url = ''

    def handle_command_request(self):
        if not zmq_poll(self._command_queue):
            error("Didn't get message")
            return

        msg = self._command_queue.recv_json()

        if 'type' not in msg:
            error("Massage invalid, please use 'type' attribute")
            (success, value) = False, 'got-bad-message'

        elif msg['type'] == self.GET_SYSTEMS:
            info("Got 'get-systems' commands.")
            (success, value) = self._agent_client_core.get_systems()

        elif msg['type'] == self.GET_CONFIGURATIONS:
            info("Got 'get-configurations' commands.")
            (success, value) = self._agent_client_core.get_configurations(msg['system_id'])

        elif msg['type'] == self.LOAD_CONFIGURATION:
            info("Got 'get-configuration' commands.")
            (success, value) = self._agent_client_core.load_configuration(msg['system_id'], msg['configuration_id'])

        elif msg['type'] == self.PUT_CONFIGURATION:
            info("Got 'put-configuration' commands.")
            (success, value) = self._agent_client_core.update_configuration(
                msg['system_id'], msg['configuration_id'], msg['configuration_content'])

        else:
            error("I don't know the type '%s', are you crazy?" % msg['type'])
            (success, value) = False, 'got-bad-message-type'

        self._command_queue.send_json({'success': success, 'value': value})

    def initialize(self):
        ctx = zmq.Context()
        self._registration_queue = ctx.socket(ZMQ_REQUEST)
        self._registration_queue.connect(self._registration_queue_url)
        self._command_queue = ctx.socket(ZMQ_REPLY)
        port = self._command_queue.bind_to_random_port('tcp://*')
        self._command_queue_url = 'tcp://%s:%s' % (self._agent_hostname, port)

    def say_hi(self):
        info('Saying hey to: %s, talk to me in %s' % (self._registration_queue_url, self._command_queue_url))
        self._registration_queue.send_json({'type': self.GREETING_MSG,
                                            'hostname': self._agent_hostname,
                                            'command_queue_address': self._command_queue_url})
        self._registration_queue.recv_json()


class AgentCore(object):
    def _get_systems(self):
        raise NotImplementedError()

    def _get_configurations(self, system_id):
        raise NotImplementedError()

    def _load_configuration(self, system_id, configuration_id):
        raise NotImplementedError()

    def _update_configuration(self, system_id, configuration_id, configuration_content):
        raise NotImplementedError()

    def get_systems(self):
        return self._get_systems()

    def get_configurations(self, system_id):
        return self._get_configurations(system_id)

    def load_configuration(self, system_id, configuration_id):
        return self._load_configuration(system_id, configuration_id)

    def update_configuration(self, system_id, configuration_id, configuration_content):
        return self._update_configuration(system_id, configuration_id, configuration_content)
