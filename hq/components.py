__author__ = 'code-museum'

import base64
import os
import subprocess

from logbook import info


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

        snorkel_metadata_dir = os.path.join(self._repository_path, '.snorkel')
        if not os.path.exists(snorkel_metadata_dir):
            os.mkdir(snorkel_metadata_dir)
            open(os.path.join(snorkel_metadata_dir, 'snorkel.conf'), 'wb').write('')
            if not self._git_manager.commit(self._repository_path, 'creating .snorkel dir'):
                os.remove(snorkel_metadata_dir)
            if not self._git_manager.push('origin', 'master'):
                os.remove(snorkel_metadata_dir)

    def get_systems(self):
        systems = set()
        for agent in filter(lambda x: not x.startswith('.'), os.listdir(self._repository_path)):
            systems.update(os.listdir(os.path.join(self._repository_path, agent)))
        return list(systems)

    def get_servers(self, system):
        servers = []
        for agent in filter(lambda x: not x.startswith('.'), os.listdir(self._repository_path)):
            if system in os.listdir(os.path.join(self._repository_path, agent)):
                servers.append(agent)
        return servers

    def get_configurations(self, agent, system):
        encoded_configurations = os.listdir(os.path.join(self._repository_path, agent, system))
        return [base64.decodestring(c) for c in encoded_configurations]

    def load_configuration(self, agent, system, configuration):
        return open(self.get_configuration_path(agent, system, configuration), 'rb').read()

    def update_configuration(self, agent, system, configuration, content):
        open(self.get_configuration_path(agent, system, configuration), 'wb').write(content)
        if self._commit_configuration_update(agent, system, configuration):
            self._git_manager.push('origin', 'master')

    def get_configuration_path(self, agent, system, configuration):
        return os.path.join(self._repository_path, agent, system, base64.encodestring(configuration).strip() + '.cfg')

    def _commit_configuration_update(self, agent, system, configuration):
        commit_message = self._create_commit_msg_for_configuration_update(agent, system, configuration)
        return self._git_manager.commit(self._repository_path, commit_message)

    @staticmethod
    def _create_commit_msg_for_configuration_update(agent, system, configuration):
        return 'update configuration: "%s" of system: %s on agent: %s' % (configuration, system, agent)

        # def get_registered_agents(self):
        #     repository_dirs = os.listdir(self._repository_path)
        #     agents = filter(lambda x: x != '.snorkel', repository_dirs)
        #     return agents

        # def create_agent_dir(self, hostname):
        #     agent_dir_path = os.path.join(self._repository_path, hostname)
        #     if not os.path.exists(agent_dir_path):
        #         os.mkdir(agent_dir_path)

        # def add_configuration(self, agent, configuration):
        #     file_name = configuration.id + '.cfg'
        #     path = os.path.join(self._repository_path, agent.server, file_name)
        #     self.create_agent_dir(agent)
        #     open(path, 'wb').write(configuration.content)
        #     self._git_manager.commit(path, 'adding configuration file: %s' % path)
        #     self._git_manager.push()


class GitManager(object):
    def __init__(self, path):
        self._path = path

    @staticmethod
    def clone(remote, path):
        GitManager.run_git_command(['clone', remote, path])
        return GitManager(path)

    @staticmethod
    def run_git_command(args=None, repo_path=None):
        info('Run git command: "%s" from dir: %s' % (' '.join(['git'] + args), repo_path))
        p = subprocess.Popen(['git'] + args, cwd=repo_path)
        return p.wait() == 0

    def pull(self):
        return self.run_git_command(['pull'], self._path)

    def push(self, remote, branch):
        return self.run_git_command(['push', remote, branch], self._path)

    def commit(self, path, msg):
        if not self.run_git_command(['add', path], self._path):
            return False
        return self.run_git_command(['commit', '-m', msg], self._path)
