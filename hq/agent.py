__author__ = 'code-museum'

import hashlib

from logbook import info

from hq.nice import ZMQ_REQUEST, SafeClientZMQSocket, SafeRandomPortServerZMQSocket, zmq_context, Commander, \
    CommandsHandler


class AgentCommander(Commander):
    def __init__(self, address, hostname):
        super(AgentCommander, self).__init__(address)
        self._address = address
        self.hostname = hostname

    def get_systems(self):
        return self._command(SnorkelAgent.GET_SYSTEMS)

    def get_configurations(self, system):
        return self._command(SnorkelAgent.GET_CONFIGURATIONS, system=system)

    def load_configuration(self, system_id, configuration_id):
        return self._command(SnorkelAgent.LOAD_CONFIGURATION, system_id=system_id, configuration_id=configuration_id)

    def update_configuration(self, system_id, configuration_id, configuration_content):
        return self._command(SnorkelAgent.PUT_CONFIGURATION, system_id=system_id, configuration_id=configuration_id,
                             configuration_content=configuration_content)

    def hash_configuration(self, system_id, configuration_id):
        return self._command(SnorkelAgent.HASH_CONFIGURATION, system_id=system_id, configuration_id=configuration_id)


class SnorkelAgent(CommandsHandler):
    GREETING_MSG = u'hello-you'
    GET_SYSTEMS = u'get-systems'
    GET_CONFIGURATIONS = u'get-configurations'
    LOAD_CONFIGURATION = u'load-configuration'
    PUT_CONFIGURATION = u'put-configuration'
    HASH_CONFIGURATION = u'hash-configuration'

    def __init__(self, client_core, agent_hostname, registration_queue_url='tcp://localhost:12345'):
        super(SnorkelAgent, self).__init__('tcp://*', SafeRandomPortServerZMQSocket)

        assert isinstance(client_core, SnorkelAgentCore)
        self._agent_client_core = client_core
        self._agent_hostname = agent_hostname
        self._registration_queue_url = registration_queue_url

        self._ctx = zmq_context()
        self._registration_queue = SafeClientZMQSocket(self._ctx, ZMQ_REQUEST, self._registration_queue_url)

        self.add_safe_command_handler(self.GET_SYSTEMS, self._agent_client_core.get_systems)
        self.add_safe_command_handler(self.GET_CONFIGURATIONS, self._agent_client_core.get_configurations)
        self.add_safe_command_handler(self.LOAD_CONFIGURATION, self._agent_client_core.load_configuration)
        self.add_safe_command_handler(self.PUT_CONFIGURATION, self._agent_client_core.update_configuration)
        self.add_safe_command_handler(self.HASH_CONFIGURATION, self.hash_configuration)

    @property
    def _command_queue_url(self):
        return self._command_handling_socket.socket_client_url(self._agent_hostname)

    def say_hi(self):
        info('Saying hey to: %s, talk to me in %s' % (self._registration_queue_url, self._command_queue_url))
        self._registration_queue.send_json({'type': self.GREETING_MSG,
                                            'hostname': self._agent_hostname,
                                            'command_queue_address': self._command_queue_url})
        self._registration_queue.receive_json()

    def hash_configuration(self, system_id, configuration_id):
        configuration_content = self._agent_client_core.load_configuration(system_id, configuration_id)[1]
        sha1 = hashlib.sha1()
        sha1.update(configuration_content)
        return True, sha1.hexdigest()


class SnorkelAgentCore(object):
    def _get_systems(self):
        raise NotImplementedError()

    def _get_configurations(self, system_id):
        raise NotImplementedError()

    def _load_configuration(self, system_id, configuration_id):
        raise NotImplementedError()

    def _update_configuration(self, system_id, configuration_id, configuration_content):
        raise NotImplementedError()

    def get_systems(self):
        return True, self._get_systems()

    def get_configurations(self, system):
        return self._get_configurations(system)

    def load_configuration(self, system_id, configuration_id):
        return self._load_configuration(system_id, configuration_id)

    def update_configuration(self, system_id, configuration_id, configuration_content):
        return self._update_configuration(system_id, configuration_id, configuration_content)
