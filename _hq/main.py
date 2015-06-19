__author__ = 'code-museum'

import zmq
from logbook import info, error
from collections import defaultdict

from _hq.nice import zmq_poll, ZMQ_REQUEST
from _hq.components import Repository
from _hq.consts import PUT_CONFIGURATION_COMMAND
from _hq.agent import AgentCommander, SnorkelAgent


class SnorkelHQCommander(object):
    def __init__(self, hq_server_name, command_queue_url='tcp://%s:12346'):
        self._command_queue_url = command_queue_url
        self._command_queue = None
        self._hq_server = hq_server_name
        self._initialized = False

    def initialize(self):
        ctx = zmq.Context()
        self._command_queue = ctx.socket(ZMQ_REQUEST)
        self._command_queue.connect(self._command_queue_url % self._hq_server)
        self._initialized = True

    def _force_initialize(self):
        if not self._initialized:
            raise Exception("Please initialize this class with initialize() function!")

    def get_systems(self):
        self._force_initialize()
        return self.command(SnorkelHQ.GET_SYSTEMS)

    def get_all_configurations(self, system):
        self._force_initialize()
        return self.command('get-all-configurations', value=system)

    def deploy_configuration(self, server, system, file_name, config):
        self._force_initialize()
        return self.command(PUT_CONFIGURATION_COMMAND,
                            value={'server': server, 'system': system, 'file_name': file_name, 'config': config})

    def command(self, type, value=None):
        self._command_queue.send_json({'type': type, 'value': value})
        if not zmq_poll(self._command_queue):
            self.initialize()
            raise Exception('Timeout after not getting answer for command %s' % type)
        return self._command_queue.recv_json()


class SnorkelHQ(object):
    GET_SYSTEMS = 'get-systems'

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
            info("Hey! it's a new agent!")
            self.add_agent(hostname=msg['hostname'], address=msg['command_queue_address'])

    def handle_commands(self):
        self._force_initialize()
        if not zmq_poll(self._command_queue):
            error("Didn't get message")
            return

        msg = self._command_queue.recv_json()

        answer = 'Failure'
        if msg['type'] == self.GET_SYSTEMS:
            info("Got command for getting all systems")
            answer = self.get_systems()
        elif msg['type'] == 'get-all-configurations':
            info("Got command for getting configurations")
            answer = self.get_configuration_files(msg['value'])
        elif msg['type'] == 'deploy-configuration':
            self.deploy_configuration(msg['value'])
        else:
            self._command_queue.send_json('got-bad-command')

        self._command_queue.send_json(answer)

    def get_systems(self):
        return self._systems.keys()

    def _force_initialize(self):
        if not self._initialized:
            raise Exception("Please initialize this class with initialize() function!")

    def initialize(self):
        ctx = zmq.Context()
        self._agents_registration_queue = ctx.socket(zmq.REP)
        self._agents_registration_queue.bind(self._agents_registration_queue_url)

        self._command_queue = ctx.socket(zmq.REP)
        self._command_queue.bind(self._command_queue_url)

        self._repository.initialize()
        self._initialized = True

    def add_agent(self, hostname, address):
        agent = AgentCommander(address, hostname)
        agent.initialize()
        self._agents[hostname] = agent
        for i, system in enumerate(agent.get_systems()):
            self._systems[system][hostname] = i
        info("Agent running on %s with systems %s was added" % (hostname, agent.get_systems()))

    def get_server_list(self, system=None):
        return [agent.server for agent in self._agents if system and system in agent.systems]

    def get_configuration_files(self, system_key):
        l = []
        for i in self._agents:
            l += self._agents[i].all_configurations(system_key)
        info("Returning configurations files: %s" % l)
        return l

    def get_configuration(self, server, system, configuration_id):
        return server.agents.configuration(system, configuration_id)

    def deploy_configuration(self, values):
        system = self._systems[values['system_key']]
        for agent in system.agents:
            agent.update_configuration()
        return True


