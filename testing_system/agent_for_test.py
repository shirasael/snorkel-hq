from hq.agent import DefaultAgentCore

__author__ = 'code-museum'

from hq import SnorkelAgent, SnorkelAgentRunner


def main():
    snorkel_agent_core = DefaultAgentCore({
        u'Banana': [u'd:\\Temp\\Sys\\sys.json'],
        u'Clementine': [u'd:\\Temp\\Tem\\tem.json']})
    snorkel_agent = SnorkelAgent(snorkel_agent_core, 'localhost')
    snorkel_agent_runner = SnorkelAgentRunner(snorkel_agent)
    snorkel_agent_runner.start()


if __name__ == '__main__':
    main()
