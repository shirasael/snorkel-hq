__author__ = 'code-museum'

from collections import defaultdict

import zmq
from logbook import info, error

from _hq.nice import zmq_poll, ZMQ_REQUEST, SafeClientZMQSocket, ZMQ_REPLY, Commander, command
from _hq.components import Repository
from _hq.agent import AgentCommander, SnorkelAgent


class SnorkelHQCommander(Commander):
    def __init__(self, hq_server_name):
        super(SnorkelHQCommander, self).__init__('tcp://%s:12346' % hq_server_name)

    def get_systems(self):
        return self._command(SnorkelHQ.GET_SYSTEMS)

    def get_servers(self, system=None):
        return self._command(SnorkelHQ.GET_SERVERS, system=system)

    def get_configurations(self, agent=None, system=None):
        return self._command(SnorkelHQ.GET_CONFIGURATIONS, agent=agent, system=system)

    def load_configuration(self, agent=None, system=None, configuration=None):
        return self._command(SnorkelHQ.LOAD_CONFIGURATION, agent=agent, system=system, configuration=configuration)


class SnorkelHQ(object):
    GET_SYSTEMS = 'get-systems'
    GET_SERVERS = 'get-servers'
    GET_CONFIGURATIONS = 'get-configurations'
    LOAD_CONFIGURATION = 'load-configuration'

    def __init__(self, repository_path, remote, agents_registration_queue_url='tcp://*:12345',
                 command_queue_url='tcp://*:12346'):
        self._agents_registration_queue_url = agents_registration_queue_url
        self._command_queue_url = command_queue_url

        self._agents_registration_queue = None
        self._command_queue = None

        self._agents = {}
        self._systems = defaultdict(dict)

        self._repository = Repository(repository_path, remote)

        self._initialized = False

    def welcome_new_agents(self):
        self._force_initialize()
        while zmq_poll(self._agents_registration_queue, 0):
            info("Got greeting from agent")
            msg = self._agents_registration_queue.recv_json()
            self._agents_registration_queue.send_json('ACK')
            if msg['type'] != SnorkelAgent.GREETING_MSG:
                continue
            info("Hey! it's an agent!")
            self.add_agent(hostname=msg['hostname'], address=msg['command_queue_address'])

    def handle_commands(self):
        self._force_initialize()
        if not zmq_poll(self._command_queue):
            error("Didn't get message")
            return

        msg = self._command_queue.recv_json()

        answer = 'Failure'
        if msg['command_type'] == self.GET_SYSTEMS:
            info("Got command for getting all systems")
            answer = self.get_systems()
        elif msg['command_type'] == self.GET_SERVERS:
            info("Got command for getting all servers (host names)")
            system = msg['parameters']['system'] if 'system' in msg['parameters'] else None
            answer = self.get_servers(system)
        elif msg['command_type'] == self.GET_CONFIGURATIONS:
            info("Got command for getting configurations of system")
            agent = msg['parameters']['agent'] if 'agent' in msg['parameters'] else None
            system = msg['parameters']['system'] if 'system' in msg['parameters'] else None
            answer = self.get_configurations(agent, system)
        elif msg['command_type'] == self.LOAD_CONFIGURATION:
            info("Got command for load configuration of system")
            agent = msg['parameters']['agent'] if 'agent' in msg['parameters'] else None
            system = msg['parameters']['system'] if 'system' in msg['parameters'] else None
            configuration = msg['parameters']['configuration'] if 'configuration' in msg['parameters'] else None
            answer = self.load_configuration(agent, system, configuration)
        else:
            self._command_queue.send_json('got-bad-command')

        self._command_queue.send_json({'status': True, 'value': answer})

    def add_agent(self, hostname, address):
        if hostname in self._agents:
            return
        agent = AgentCommander(address, hostname)
        agent.initialize()
        self._agents[hostname] = agent
        for i, system in enumerate(agent.get_systems()):
            self._systems[system][hostname] = i
        info("Agent running on %s with systems %s was added" % (hostname, agent.get_systems()))

    def get_systems(self):
        info("get_systems called, returning: %s" % self._systems.keys())
        return self._systems.keys()

    def get_servers(self, system=None):
        info("get_servers called with parameter system=%s" % repr(system))
        return [hostname for hostname, agent in self._agents.iteritems() if
                not system or hostname in self._systems[system]]

    def _force_initialize(self):
        if not self._initialized:
            raise Exception("Please initialize this class with initialize() function!")

    def initialize(self):
        ctx = zmq.Context()
        self._agents_registration_queue = ctx.socket(ZMQ_REPLY)
        self._agents_registration_queue.bind(self._agents_registration_queue_url)

        self._command_queue = ctx.socket(ZMQ_REPLY)
        self._command_queue.bind(self._command_queue_url)

        self._repository.initialize()
        self._initialized = True

    def get_configurations(self, agent, system):
        info("Returning configurations paths")
        return self._agents[agent].get_configurations(self._systems[system][agent])

    def load_configuration(self, agent, system, configuration):
        configuration_key = self.get_configurations(agent, system).index(configuration)
        return self._agents[agent].load_configuration(self._systems[system][agent], configuration_key)

    def deploy_configuration(self, values):
        system = self._systems[values['system_key']]
        for agent in system.agents:
            agent.update_configuration()
        return True
