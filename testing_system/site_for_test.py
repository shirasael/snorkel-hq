__author__ = 'code-museum'

from hq import SnorkelHQCommander


def main():
    snorkel_hq_commander = SnorkelHQCommander('localhost')
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_systems()
    systems = snorkel_hq_commander.get_systems()
    print systems
    banana_servers = snorkel_hq_commander.get_servers(u'Clementine')
    print banana_servers
    banana_configurations = snorkel_hq_commander.get_configurations(u'localhost', u'Banana')
    print banana_configurations
    print
    if not banana_configurations:
        return
    print snorkel_hq_commander.load_configuration(u'localhost', u'Banana', banana_configurations[0])
    # print snorkel_hq_commander.load_configuration(None, None, None)
    snorkel_hq_commander.update_configuration(u'localhost', u'Banana', banana_configurations[0], '{}')
    print snorkel_hq_commander.load_configuration(u'localhost', u'Banana', banana_configurations[0])

if __name__ == '__main__':
    main()
