from _hq.main import SnorkelHQCommander

__author__ = 'code-museum'

def main():
    snorkel_hq_commander = SnorkelHQCommander('localhost')
    snorkel_hq_commander.initialize()
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_servers()

if __name__ == '__main__':
    main()
