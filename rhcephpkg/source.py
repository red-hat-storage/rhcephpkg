import subprocess
from tambo import Transport
import rhcephpkg.log as log


class Source(object):
    help_menu = 'build a source package on the local system'
    _help = """
Build a source package on the local system.
"""
    name = 'source'

    def __init__(self, argv):
        self.argv = argv

    def main(self):
        self.parser = Transport(self.argv)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        self._run()

    def help(self):
        return self._help

    def _run(self):
        """ Build a source package on the local system. """
        cmd = ['gbp', 'buildpackage', '--git-tag', '--git-retag', '-S',
               '-us', '-uc']
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)
