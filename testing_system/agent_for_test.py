__author__ = 'code-museum'

import json

from hq.agent import DefaultAgentCore
from hq import SnorkelAgent, SnorkelAgentRunner


def main():

    configuration = json.load(open('agent_configuration.json', 'rb'))

    snorkel_agent_core = DefaultAgentCore(configuration)
    snorkel_agent = SnorkelAgent(snorkel_agent_core, 'localhost')
    snorkel_agent_runner = SnorkelAgentRunner(snorkel_agent)
    snorkel_agent_runner.start()


if __name__ == '__main__':
    main()
