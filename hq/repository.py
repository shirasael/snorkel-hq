__author__ = 'code-museum'

import base64
import hashlib
import os

from logbook import info

from hq.nice.git import GitManager


class SnorkelRepository(object):
    def __init__(self, repository_path, remote):
        self._repository_path = repository_path
        self._remote = remote
        self._repository = None
        self._git_manager = None
        self._remote_git_manager = None

    def initialize(self):
        self._initialize_remote()

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

    def _initialize_remote(self):
        if not os.path.exists(self._remote):
            info(u"Can't find remote, creating directory!")
            os.mkdir(self._remote)

        if not os.path.exists(os.path.join(self._remote, 'refs')):
            self._remote_git_manager = GitManager.init(self._remote, bare=True)
        else:
            self._remote_git_manager = GitManager(self._remote)

    def get_systems(self):
        systems = set()
        for agent in filter(lambda x: not x.startswith('.'), os.listdir(self._repository_path)):
            systems.update(os.listdir(os.path.join(self._repository_path, agent)))
        return list(systems)

    def get_servers(self, system=None):
        servers = []
        for hostname in filter(lambda x: not x.startswith('.'), os.listdir(self._repository_path)):
            if not system or system in os.listdir(os.path.join(self._repository_path, hostname)):
                servers.append(hostname)
        return servers

    def has_server(self, hostname):
        return os.path.exists(os.path.join(self._repository_path, hostname))

    def add_server(self, hostname):
        if os.path.exists(os.path.join(self._repository_path, hostname)):
            raise Exception('Server %s is already exists in repository!' % hostname)
        os.mkdir(os.path.join(self._repository_path, hostname))

    def add_system(self, hostname, system):
        if not os.path.exists(os.path.join(self._repository_path, hostname)):
            raise Exception("Can't find hostname %s in repository!" % hostname)
        if os.path.exists(os.path.join(self._repository_path, hostname, system)):
            raise Exception('System %s is already exists in repository!' % system)
        os.mkdir(os.path.join(self._repository_path, hostname, system))

    def has_system(self, hostname, system):
        return os.path.exists(os.path.join(self._repository_path, hostname, system))

    def get_configurations(self, agent, system):
        encoded_configurations = os.listdir(os.path.join(self._repository_path, agent, system))
        return [base64.decodestring(c) for c in encoded_configurations]

    def load_configuration(self, agent, system, configuration):
        return open(self._get_configuration_path(agent, system, configuration), 'rb').read()

    def update_configuration(self, agent, system, configuration, content):
        open(self._get_configuration_path(agent, system, configuration), 'wb').write(content)
        if self._commit_configuration_update(agent, system, configuration):
            self._git_manager.push('origin', 'master')

    def add_configuration(self, hostname, system, configuration, content):
        if self.has_configuration(hostname, system, configuration):
            raise Exception("Configuration %s is already exists in repository!" % configuration)
        self.update_configuration(hostname, system, configuration, content)

    def hash_configuration(self, hostname, system, configuration):
        configuration_content = self.load_configuration(hostname, system, configuration)
        sha1 = hashlib.sha1()
        sha1.update(configuration_content)
        return sha1.hexdigest()

    def has_configuration(self, hostname, system, configuration):
        return os.path.exists(self._get_configuration_path(hostname, system, configuration))

    def _get_configuration_path(self, agent, system, configuration):
        return os.path.join(self._repository_path, agent, system, base64.encodestring(configuration).strip() + '.cfg')

    def _commit_configuration_update(self, agent, system, configuration):
        commit_message = self._create_commit_msg_for_configuration_update(agent, system, configuration)
        return self._git_manager.commit(self._repository_path, commit_message)

    @staticmethod
    def _create_commit_msg_for_configuration_update(agent, system, configuration):
        return 'update configuration: "%s" of system: %s on agent: %s' % (configuration, system, agent)
