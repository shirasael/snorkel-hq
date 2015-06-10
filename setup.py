__author__ = 'code-museum'

from setuptools import setup

REQUIREMENTS = ['pyzmq', 'logbook']

setup(
    name='sonrkel-hq',
    version='0.0.1',
    py_modules=['bytes'],
    packages=['_hq'],
    install_requires=REQUIREMENTS,
    url='https://github.com/shirasael/snorkel-hq',
    license='GPLv3',
    author='code-museum',
    author_email='code-museum@users.noreply.github.com',
    description='',
    keywords=""
)
