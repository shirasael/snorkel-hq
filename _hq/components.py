import os
import subprocess
from logbook import info
import zmq
from _hq import consts

__author__ = '$Author'


class System(object):
    def __init__(self, name, id, configurations=None, agents=None):
        self.agents = agents if agents is not None else []
        self.configurations = configurations if configurations is not None else []
        self.id = id
        self.name = name


class Configurations(object):
    def __init__(self, id, name, content):
        self.id = id
        self.name = name
        self.content = content


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
            self._git_manager.commit(self._repository_path, 'creating .snorkel dir')
            self._git_manager.push('origin', 'master')

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
        p.wait()

    def pull(self):
        self.run_git_command(['pull'], self._path)

    def push(self, remote, branch):
        self.run_git_command(['push', remote, branch], self._path)

    def commit(self, path, msg):
        self.run_git_command(['add', path], self._path)
        self.run_git_command(['commit', '-m', msg], self._path)