__author__ = 'code-museum'

from collections import defaultdict

import zmq
from logbook import info

from _hq.nice import zmq_poll, ZMQ_REPLY, Commander, CommandsHandler
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


class SnorkelHQ(CommandsHandler):
    GET_SYSTEMS = 'get-systems'
    GET_SERVERS = 'get-servers'
    GET_CONFIGURATIONS = 'get-configurations'
    LOAD_CONFIGURATION = 'load-configuration'

    def __init__(self, repository_path, remote, agents_registration_queue_url='tcp://*:12345',
                 command_queue_url='tcp://*:12346'):
        super(SnorkelHQ, self).__init__(command_queue_url)

        self.add_command_handler(self.GET_SYSTEMS,
                                 lambda: (True, self.get_systems()))
        self.add_command_handler(self.GET_SERVERS,
                                 lambda *args, **kwargs: (True, self.get_servers(*args, **kwargs)))
        self.add_command_handler(self.GET_CONFIGURATIONS,
                                 lambda *args, **kwargs: (True, self.get_configurations(*args, **kwargs)))
        self.add_command_handler(self.LOAD_CONFIGURATION,
                                 lambda *args, **kwargs: (True, self.load_configuration(*args, **kwargs)))

        self._agents_registration_queue_url = agents_registration_queue_url
        self._agents_registration_queue = None

        self._agents = {}
        self._systems = defaultdict(dict)

        self._repository = Repository(repository_path, remote)

        self._initialized = False

    def initialize(self):
        ctx = zmq.Context()
        self._agents_registration_queue = ctx.socket(ZMQ_REPLY)
        self._agents_registration_queue.bind(self._agents_registration_queue_url)

        self._repository.initialize()
        self._initialized = True

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

    def add_agent(self, hostname, address):
        if hostname in self._agents:
            return
        agent = AgentCommander(address, hostname)
        agent.initialize()
        self._repository.create_agent_dir(hostname)
        self._agents[hostname] = agent
        for i, system in enumerate(agent.get_systems()):
            self._systems[system][hostname] = i
        info("Agent running on %s with systems %s was added" % (hostname, agent.get_systems()))

    def get_systems(self):
        info("get_systems called, returning: %s" % self._systems.keys())
        # return self._systems.keys()
        return self._repository.get_systems()

    def get_servers(self, system=None):
        info("get_servers called with parameter system=%s" % repr(system))
        return self._repository.get_servers(system)
        # return [hostname for hostname, agent in self._agents.iteritems() if
        #         not system or hostname in self._systems[system]]

    def _force_initialize(self):
        if not self._initialized:
            raise Exception("Please initialize this class with initialize() function!")

    def get_configurations(self, agent, system):
        info("Returning configurations paths")
        return self._repository.get_configurations(agent, system)
        # return self._agents[agent].get_configurations(self._systems[system][agent])

    def load_configuration(self, agent, system, configuration):
        configuration_key = self.get_configurations(agent, system).index(configuration)
        return self._repository.load_configuration(agent, system, configuration)
        # return self._agents[agent].load_configuration(self._systems[system][agent], configuration_key)

    def deploy_configuration(self, values):
        system = self._systems[values['system_key']]
        for agent in system.agents:
            agent.update_configuration()
        return True
