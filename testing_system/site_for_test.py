from _hq.main import SnorkelHQCommander

__author__ = 'code-museum'

def main():
    snorkel_hq_commander = SnorkelHQCommander('localhost')
    print snorkel_hq_commander.get_systems()

if __name__ == '__main__':
    main()
