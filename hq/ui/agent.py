from argparse import ArgumentParser

__author__ = 'code-museum'


def main():
    argument_parser = ArgumentParser(description="Snorkel Agent")
    argument_parser.add_argument('configuration', metavar='1', type=file)

    arguments = argument_parser.parse_args()

    print arguments.configuration
