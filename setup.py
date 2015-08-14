__author__ = 'code-museum'

from setuptools import setup

REQUIREMENTS = ['pyzmq', 'logbook']

setup(
    name='snorkel-hq',
    version='0.0.1',
    packages=['hq'],
    install_requires=REQUIREMENTS,
    url='https://github.com/shirasael/snorkel-hq',
    license='GPLv3',
    author='code-museum',
    author_email='code-museum@users.noreply.github.com',
    description='',
    keywords=""
)
