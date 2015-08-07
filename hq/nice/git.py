import subprocess
from logbook import info

__author__ = '$Author'


class GitManager(object):
    def __init__(self, path):
        self._path = path

    @staticmethod
    def init(path, bare=False):
        command = [u'init']
        if bare:
            command += [u'--bare']
        GitManager.run_git_command(command, path)
        return GitManager(path)

    @staticmethod
    def clone(remote, path):
        GitManager.run_git_command(['clone', remote, path])
        return GitManager(path)

    @staticmethod
    def run_git_command(args=None, repo_path=None):
        info('Run git command: "%s" from dir: %s' % (' '.join(['git'] + args), repo_path))
        p = subprocess.Popen(['git'] + args, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.wait() == 0, p.stdout.read()

    def pull(self):
        status, standard_output = self.run_git_command(['pull'], self._path)
        return status

    def push(self, remote, branch):
        status, standard_output = self.run_git_command(['push', remote, branch], self._path)
        return status

    def commit(self, path, msg):
        status, standard_output = self.run_git_command(['add', path], self._path)
        if not status:
            return status
        status, standard_output = self.run_git_command(['commit', '-m', msg], self._path)
        print standard_output
        return status