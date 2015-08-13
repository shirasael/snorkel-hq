__author__ = 'code-museum'

from logbook import error

from hq import SnorkelAgentCore, SnorkelAgent, SnorkelAgentRunner


class SystemTestSnorkelAgentCore(SnorkelAgentCore):
    def __init__(self):
        super(SystemTestSnorkelAgentCore, self).__init__()

        self.systems_to_configurations = {
            'Banana': ['d:\\Temp\\Sys\\sys.json'],
            'Clementine': ['d:\\Temp\\Tem\\tem.json']
        }

        self.systems = list(self.systems_to_configurations.keys())
        self.configurations = reduce(list.__add__, self.systems_to_configurations.values())

    def _get_systems(self):
        return self.systems

    def _get_configurations(self, system):
        if system not in self.systems_to_configurations:
            error("I don't know system '%s', is it nice?" % system)
            return False, None
        return True, self.systems_to_configurations[system]

    def _update_configuration(self, system_id, configuration_id, configuration_content):
        # if system_id < 0 or system_id > len(self.systems) - 1:
        #     error("I don't know system id %s, is it nice?" % system_id)
        #     return False, None
        # if configuration_id < 0 or configuration_id > len(self.configurations) -1:
        #     error("I doesn't have this configuration %s, how much it costs?" % self.configurations)
        #     return False, None
        open(configuration_id, 'wb').write(configuration_content)
        return True, None

    def _load_configuration(self, system_id, configuration):
        return True, open(configuration, 'rb').read()


def main():
    snorkel_agent_core = SystemTestSnorkelAgentCore()
    snorkel_agent = SnorkelAgent(snorkel_agent_core, 'localhost')
    snorkel_agent_runner = SnorkelAgentRunner(snorkel_agent)
    snorkel_agent_runner.start()

if __name__ == '__main__':
    main()
