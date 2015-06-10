__author__ = 'code-museum'

from _hq.client import AgentCore, SnorkelAgent, SnorkelAgentRunner


class SnorkelAgentCore(AgentCore):
    def __init__(self):
        super(SnorkelAgentCore, self).__init__()
        self.configurations_to_system = {
            'Sys': ['d:\\Temp\\Sys\\sys.json'],
            'Tem': ['d:\\Temp\\Tem\\tem.json']
        }

    def _get_systems(self):
        return self.configurations_to_system.keys()

    def _get_configurations(self, system):
        return self.configurations_to_system[system]


def main():
    snorkel_agent_core = SnorkelAgentCore()
    snorkel_agent = SnorkelAgent(snorkel_agent_core, 'localhost')
    snorkel_agent_runner = SnorkelAgentRunner(snorkel_agent)
    snorkel_agent_runner.start()

if __name__ == '__main__':
    main()