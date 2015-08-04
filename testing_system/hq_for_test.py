__author__ = 'code-museum'

from hq.main import SnorkelHQ
from hq.runners import SnorkelHQRunner


def main():
    snorkel_hq = SnorkelHQ('D:\\Temp\\snorkel_repository', 'D:\\Temp\\snorkel_remote')
    snorkel_hq_worker = SnorkelHQRunner(snorkel_hq)
    snorkel_hq_worker.start()


if __name__ == '__main__':
    main()
