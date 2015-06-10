__author__ = 'code-museum'


from hq import SnorkelHQRunner

def main():
    snorkel_hq_worker = SnorkelHQRunner('D:\\Temp\\snorkel_repository', 'D:\\Temp\\snorkel_remote')
    snorkel_hq_worker.start()


if __name__ == '__main__':
    main()
