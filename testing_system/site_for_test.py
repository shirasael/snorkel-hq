from _hq.main import SnorkelHQCommander

__author__ = 'code-museum'

def main():
    snorkel_hq_commander = SnorkelHQCommander('localhost')
    print snorkel_hq_commander.get_systems()
    print snorkel_hq_commander.get_servers(u'Banana')
    banana_configurations = snorkel_hq_commander.get_configurations(u'Banana')
    print banana_configurations

    for i in snorkel_hq_commander.load_configuration(u'Banana', banana_configurations[0]):
        print 'configuration: %s' % banana_configurations[0]
        print i

if __name__ == '__main__':
    main()
