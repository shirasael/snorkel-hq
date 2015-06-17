__author__ = 'code-museum'

from logbook import error

from _hq.runners import SnorkelAgentRunner
from _hq.agent import AgentCore, SnorkelAgent


class SnorkelAgentCore(AgentCore):
    def __init__(self):
        super(SnorkelAgentCore, self).__init__()

        self.systems_to_configurations = {
            'Banana': ['d:\\Temp\\Sys\\sys.json'],
            'Clementine': ['d:\\Temp\\Tem\\tem.json']
        }

        self.systems = list(self.systems_to_configurations.keys())
        self.configurations = reduce(list.__add__, self.systems_to_configurations.values())

    def _get_systems(self):
        return True, self.systems

    def _get_configurations(self, system_id):
        if system_id < 0 or system_id > len(self.systems) - 1:
            error("I don't know system id %s, is it nice?" % system_id)
            return False, None
        return True, self.systems_to_configurations[self.systems[system_id]]

    def _put_configuration(self, system_id, configuration_id, configuration_content):
        if system_id < 0 or system_id > len(self.systems) - 1:
            error("I don't know system id %s, is it nice?" % system_id)
            return False, None
        if configuration_id < 0 or configuration_id > len(self.configurations) -1:
            error("I doesn't have this configuration %s, how much it costs?" % self.configurations)
            return False, None
        open(self.configurations[configuration_id], 'wb').write(configuration_content)
        return True, None

    def _get_configuration(self, system_id, configuration_id):
        if system_id < 0 or system_id > len(self.systems) - 1:
            error("I don't know system id %s, is it nice?" % system_id)
            return False, None
        if configuration_id < 0 or configuration_id > len(self.configurations) -1:
            error("I doesn't have this configuration %s, how much it costs?" % self.configurations)
            return False, None
        return True, open(self.configurations[configuration_id], 'rb').read()


def main():
    snorkel_agent_core = SnorkelAgentCore()
    snorkel_agent = SnorkelAgent(snorkel_agent_core, 'localhost')
    snorkel_agent_runner = SnorkelAgentRunner(snorkel_agent)
    snorkel_agent_runner.start()

if __name__ == '__main__':
    main()