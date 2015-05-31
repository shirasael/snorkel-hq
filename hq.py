__author__ = 'code-museum'

import _hq
import _hq.client
from _hq import consts

import os
import subprocess
import zmq

AgentClient = _hq.client.AgentClient
AgentClientCore = _hq.client.AgentClientCore


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
    def __init__(self, id, content):
        self.id = id
        self.content = content


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
        self._command_queue.send_json({'type': consts.GET_SYSTEM_TYPE})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def all_configurations(self, system):
        self._command_queue.send_json({'type': consts.GET_ALL_CONFIGURATIONS_TYPE, 'system': system})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def configuration(self, system, configuration_id):
        self._command_queue.send_json(
            {'type': consts.GET_CONFIGURATION_TYPE, 'system': system, 'configuration_id': configuration_id})
        answer = self._command_queue.recv_json()
        if answer['success']:
            return answer['value']
        return []

    def update_configuration(self, system, configuration):
        self._command_queue.send_json(
            {'type': consts.PUT_CONFIGURATION_TYPE, 'system': system,
             'configuration_id': configuration.id,
             'configuration_content': configuration.content})
        answer = self._command_queue.recv_json()
        if answer['success']:
            print 'Configuration update succeed'


class SnorkelHQ(object):
    def __init__(self, repository_path, remote):
        self._agents = []
        self._servers_agents = {}
        self._repository = Repository(repository_path, remote)
        self._agents_registration_queue = None

    def initialize(self):
        ctx = zmq.Context()
        self._agents_registration_queue = ctx.socket(zmq.REP)
        self._agents_registration_queue.bind('tcp://*:12345')
        self._repository.initialize()

    def handle_registration_message(self):
        if self._agents_registration_queue.poll(3000) != zmq.POLLIN:
            print "Didn't get message"
            return

        msg = self._agents_registration_queue.recv_json()
        self._agents_registration_queue.send_json('ACK')
        if msg['type'] != consts.GREETING_TYPE:
            return
        self.add_agent(server_name=msg['server'], address=msg['command_queue_address'])

    def get_system(self):
        systems = []
        for agent in self._agents:
            systems += agent.systems
        return systems

    def get_server_list(self, system=None):
        return [agent.server for agent in self._agents if system and system in agent.systems]

    def get_configuration_files(self, server, system):
        return self._servers_agents[server].all_configurations(system)

    def get_configuration(self, server, system, configuration_id):
        return self._servers_agents[server].configuration(system, configuration_id)

    def add_agent(self, server_name, address):
        agent = AgentServer(server_name, address)
        agent.initialize()
        self._agents.append(agent)
        self._servers_agents[agent.server] = agent
