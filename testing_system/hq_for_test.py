__author__ = 'code-museum'

from hq import SnorkelHQ, SnorkelHQRunner


def main():
    snorkel_hq = SnorkelHQ(u'D:\\Temp\\SnorkelSystemTest\\snorkel_repository',
                           u'D:\\Temp\\SnorkelSystemTest\\snorkel_remote')
    snorkel_hq_worker = SnorkelHQRunner(snorkel_hq)
    snorkel_hq_worker.start()


if __name__ == '__main__':
    main()
