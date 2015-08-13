__author__ = 'code-museum'

from datetime import datetime, timedelta

from hq.main import SnorkelHQ


class SnorkelAgentRunner(object):
    def __init__(self, agent):
        self._agent = agent

    def start(self):
        last_time_welcoming = None
        while True:
            if not last_time_welcoming or last_time_welcoming <= datetime.now() - timedelta(seconds=15):
                self._agent.say_hi()
                last_time_welcoming = datetime.now()
            self._agent.handle_commands()


class SnorkelHQRunner(object):
    def __init__(self, snorkel_hq):
        assert isinstance(snorkel_hq, SnorkelHQ)
        self._snorkel_hq = snorkel_hq

    def start(self):
        self._snorkel_hq.initialize()
        while True:
            self._snorkel_hq.handle_agents_registration()
            self._snorkel_hq.update_repository()
            self._snorkel_hq.handle_commands()
