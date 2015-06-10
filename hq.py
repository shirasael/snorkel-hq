import logbook
from logbook import warn, info, debug

__author__ = 'code-museum'

import _hq
import _hq.client
from _hq import consts

import os
import subprocess
import zmq

AgentClient = _hq.client.SnorkelAgent
AgentCore = _hq.client.AgentCore


class GitManager(object):
    def __init__(self, path):
        self._path = path

    @staticmethod
    def clone(remote, path):
        GitManager.run_git_command(['clone', remote, path])
        return GitManager(path)

    @staticmethod
    def run_git_command(args=None, repo_path=None):
        print 'Run git command: "%s" from dir: %s' % (' '.join(['git'] + args), repo_path)
        p = subprocess.Popen(['git'] + args, cwd=repo_path)
        p.wait()

    def pull(self):
        self.run_git_command(['pull'], self._path)

    def push(self):
        self.run_git_command(['push'], self._path)

    def commit(self, path, msg):
        self.run_git_command(['add', path], self._path)
        self.run_git_command(['commit', '-m', msg], self._path)


class Repository(object):
    def __init__(self, repository_path, remote):
        self._repository_path = repository_path
        self._remote = remote
        self._repository = None
        self._git_manager = None

    def initialize(self):
        if not os.path.exists(self._repository_path):
            self._git_manager = GitManager.clone(self._remote, self._repository_path)
        self._git_manager = GitManager(self._repository_path)
        self._git_manager.pull()

    def create_agent_dir(self, agent):
        agent_dir_path = os.path.join(self._repository_path, agent.server)
        if not os.path.exists(agent_dir_path):
            os.mkdir(agent_dir_path)

    def add_configuration(self, agent, configuration):
        file_name = configuration.id + '.cfg'
        path = os.path.join(self._repository_path, agent.server, file_name)
        self.create_agent_dir(agent)
        open(path, 'wb').write(configuration.content)
        self._git_manager.commit(path, 'adding configuration file: %s' % path)
        self._git_manager.push()


class Configurations(object):
    def __init__(self, id, name, content):
        self.id = id
        self.name = name
        self.content = content


class System(object):
    def __init__(self, name, id, configurations=None, agents=None):
        self.agents = agents if agents is not None else []
        self.configurations = configurations if configurations is not None else []
        self.id = id
        self.name = name


class AgentServer(object):
    def __init__(self, server_name, address):
        self.server = server_name
        self._systems = []
        self._address = address
        self._command_queue = None

    def initialize(self):
        ctx = zmq.Context()
        self._command_queue = ctx.socket(zmq.REQ)
        self._command_queue.connect(self._address)

    @property
    def systems(self):
        self._command_queue.send_json({'type': consts.GET_SYSTEMS_MESSAGE})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def all_configurations(self, system):
        self._command_queue.send_json({'type': consts.GET_ALL_CONFIGURATIONS_MESSAGE, 'system': system})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def configuration(self, system, configuration_id):
        self._command_queue.send_json(
            {'type': consts.GET_CONFIGURATION_COMMAND, 'system': system, 'configuration_id': configuration_id})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def update_configuration(self, system, configuration):
        self._command_queue.send_json(
            {'type': consts.PUT_CONFIGURATION_COMMAND, 'system': system,
             'configuration_id': configuration.id,
             'configuration_content': configuration.content})
        answer = self._command_queue.recv_json()
        if answer['success']:
            print 'Configuration update succeed'


class SnorkelHQ(object):
    def __init__(self, repository_path, remote, agents_registration_queue_url='tcp://*:12345',
                 command_queue_url='tcp://*:12346'):
        self._agents_registration_queue_url = agents_registration_queue_url
        self._command_queue_url = command_queue_url

        self._agents_registration_queue = None
        self._command_queue = None

        self._agents = {}
        self._systems = {}

        self._repository = Repository(repository_path, remote)

        self._initialized = False

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

    def welcome_new_agents(self):
        self._force_initialize()
        while self._agents_registration_queue.poll(0) == zmq.POLLIN:
            msg = self._agents_registration_queue.recv_json()
            self._agents_registration_queue.send_json('ACK')
            if msg['type'] != consts.GREETING_TYPE:
                continue
            info("Hey! it's a new agent!")
            self.add_agent(server_name=msg['server'], address=msg['command_queue_address'])

    def add_agent(self, server_name, address):
        agent = AgentServer(server_name, address)
        agent.initialize()
        self._agents[server_name] = agent
        for system in agent.systems:
            self._systems[system] = {'name': system, 'agent': agent}

    def handle_commands(self):
        self._force_initialize()
        if self._command_queue.poll(3000) != zmq.POLLIN:
            debug("Didn't get message")
            return

        msg = self._command_queue.recv_json()
        if msg['type'] == consts.GET_ALL_SYSTEMS:
            return self.get_all_sysatems_names()
        elif msg['type'] == consts.GET_ALL_CONFIGURATIONS_MESSAGE:
            return self.get_configuration_files(msg['value'])
        elif msg['type'] == consts.DEPLOY_CONFIGURATION_MESSAGE:
            self.deploy_configuration(msg['value'])
        else:
            self._command_queue.send_json('GOT_BAD_COMMAND')

    def get_system(self):
        systems = []
        for agent in self._agents:
            systems += agent.systems
        return systems

    def get_server_list(self, system=None):
        return [agent.server for agent in self._agents if system and system in agent.systems]

    def get_configuration_files(self, system_key):
        return self._systems[system_key].configurations

    def get_configuration(self, server, system, configuration_id):
        return server.agents.configuration(system, configuration_id)

    def deploy_configuration(self, values):
        system = self._systems[values['system_key']]
        for agent in system.agents:
            agent.update_configuration()
        return True

    def get_all_sysatems_names(self):
        return self._systems.keys()


class SnorkelHQRunner(object):
    def __init__(self, repository_path, remote):
        self._snorkel_hq = SnorkelHQ(repository_path, remote)

    def start(self):
        self._snorkel_hq.initialize()
        while True:
            self._snorkel_hq.welcome_new_agents()
            self._snorkel_hq.handle_commands()

