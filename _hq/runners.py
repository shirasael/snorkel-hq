__author__ = 'code-museum'

from datetime import datetime, timedelta
from _hq.main import SnorkelHQ


class SnorkelAgentRunner(object):
    def __init__(self, agent):
        self._agent = agent

    def start(self):
        last_time_welcoming = None
        self._agent.initialize()
        while True:
            if not last_time_welcoming or last_time_welcoming <= datetime.now() - timedelta(seconds=15):
                self._agent.say_hi()
                last_time_welcoming = datetime.now()
            self._agent.handle_command_request()


class SnorkelHQRunner(object):
    def __init__(self, snorkel_hq):
        self._snorkel_hq = snorkel_hq

    def start(self):
        self._snorkel_hq.initialize()
        while True:
            self._snorkel_hq.welcome_new_agents()
            # self._snorkel_hq.handle_commands()