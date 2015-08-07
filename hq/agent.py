﻿from hq.nice.communication import Commander, CommandsHandler
from hq.nice.zeromq import zmq_context

__author__ = 'code-museum'

from logbook import info, error

from hq.nice import ZMQ_REQUEST, ZMQ_REPLY, zmq_poll, SafeClientZMQSocket, SafeRandomPortServerZMQSocket


class AgentCommander(Commander):
    def __init__(self, address, hostname):
        super(AgentCommander, self).__init__(address)
        self._address = address
        self._hostname = hostname
        # self._command_queue = SafeClientZMQSocket(zmq_context(), ZMQ_REQUEST, self._address)

    # def command(self, msg_type, **values):
    #     command = {'type': msg_type}
    #     if values:
    #         command.update(values)
    #
    #     self._command_queue.send_json(command)
    #     if not zmq_poll(self._command_queue, 3000):
    #         error("Timeout while waiting for answer to command: %s" % msg_type)
    #         self._command_queue.initialize()
    #     answer = self._command_queue.receive_json()
    #     if 'success' not in answer or 'value' not in answer:
    #         error("Answer format is wrong, use 'success' and 'value' attributes")
    #         return None
    #     if not answer['success']:
    #         error("Command not succeeded, because of %s" % answer['value'])
    #         return None
    #     return answer

    def get_systems(self):
        return self._command(SnorkelAgent.GET_SYSTEMS)

    def get_configurations(self, system_id):
        return self._command(SnorkelAgent.GET_CONFIGURATIONS, system_id=system_id)

    def load_configuration(self, system_id, configuration_id):
        return self._command(SnorkelAgent.LOAD_CONFIGURATION, system_id=system_id, configuration_id=configuration_id)

    def update_configuration(self, system_id, configuration_id, configuration_content):
        return self._command(SnorkelAgent.PUT_CONFIGURATION, system_id=system_id, configuration_id=configuration_id,
                             configuration_content=configuration_content)


class SnorkelAgent(CommandsHandler):
    GREETING_MSG = u'hello-you'
    GET_SYSTEMS = u'get-systems'
    GET_CONFIGURATIONS = u'get-configurations'
    LOAD_CONFIGURATION = u'load-configuration'
    PUT_CONFIGURATION = u'put-configuration'

    def __init__(self, client_core, agent_hostname, registration_queue_url='tcp://localhost:12345'):
        super(SnorkelAgent, self).__init__('tcp://*', SafeRandomPortServerZMQSocket)

        assert isinstance(client_core, SnorkelAgentCore)
        self._agent_client_core = client_core
        self._agent_hostname = agent_hostname
        self._registration_queue_url = registration_queue_url

        self._ctx = zmq_context()
        self._registration_queue = SafeClientZMQSocket(self._ctx, ZMQ_REQUEST, self._registration_queue_url)
        # self._command_queue = SafeRandomPortServerZMQSocket(self._ctx, ZMQ_REPLY, 'tcp://*')

        self.add_safe_command_handler(self.GET_SYSTEMS, self._agent_client_core._get_systems)
        self.add_safe_command_handler(self.GET_CONFIGURATIONS, self._agent_client_core.get_configurations)
        self.add_safe_command_handler(self.LOAD_CONFIGURATION, self._agent_client_core.load_configuration)
        self.add_safe_command_handler(self.PUT_CONFIGURATION, self._agent_client_core.update_configuration)

    @property
    def _command_queue_url(self):
        return self._command_handling_socket.socket_client_url(self._agent_hostname)

    # def handle_command_request(self):
    #     if not zmq_poll(self._command_queue):
    #         error("Didn't get message")
    #         return
    #
    #     msg = self._command_queue.receive_json()
    #
    #     if 'type' not in msg:
    #         error("Massage invalid, please use 'type' attribute")
    #         (success, value) = False, 'got-bad-message'
    #
    #     elif msg['type'] == self.GET_SYSTEMS:
    #         info("Got 'get-systems' commands.")
    #         (success, value) = self._agent_client_core.get_systems()
    #
    #     elif msg['type'] == self.GET_CONFIGURATIONS:
    #         info("Got 'get-configurations' commands.")
    #         (success, value) = self._agent_client_core.get_configurations(msg['system_id'])
    #
    #     elif msg['type'] == self.LOAD_CONFIGURATION:
    #         info("Got 'get-configuration' commands.")
    #         (success, value) = self._agent_client_core.load_configuration(msg['system_id'], msg['configuration_id'])
    #
    #     elif msg['type'] == self.PUT_CONFIGURATION:
    #         info("Got 'put-configuration' commands.")
    #         (success, value) = self._agent_client_core.update_configuration(
    #             msg['system_id'], msg['configuration_id'], msg['configuration_content'])
    #
    #     else:
    #         error("I don't know the type '%s', are you crazy?" % msg['type'])
    #         (success, value) = False, 'got-bad-message-type'
    #
    #     self._command_queue.send_json({'success': success, 'value': value})

    def say_hi(self):
        info('Saying hey to: %s, talk to me in %s' % (self._registration_queue_url, self._command_queue_url))
        self._registration_queue.send_json({'type': self.GREETING_MSG,
                                            'hostname': self._agent_hostname,
                                            'command_queue_address': self._command_queue_url})
        self._registration_queue.receive_json()


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

    def get_configurations(self, system_id):
        return self._get_configurations(system_id)

    def load_configuration(self, system_id, configuration_id):
        return self._load_configuration(system_id, configuration_id)

    def update_configuration(self, system_id, configuration_id, configuration_content):
        return self._update_configuration(system_id, configuration_id, configuration_content)
