import os
import subprocess
from six.moves import configparser
from tambo import Transport
import rhcephpkg.util as util


class Clone(object):
    help_menu = 'clone a package from dist-git'
    _help = """
Clone a package from dist-git. Your SSH key must be set up in Gerrit.

Positional Arguments:

[package]  The name of the package to clone.
"""
    name = 'clone'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            pkg = self.parser.unknown_commands[0]
        except IndexError:
            self.help()
        self._run(pkg)

    def help(self):
        return self._help

    def _run(self, pkg):
        """ Clone a package from dist-git. """
        if os.path.exists(pkg):
            raise SystemExit('%s already exists in current working directory.',
                             pkg)
        configp = util.config()
        try:
            user = configp.get('rhcephpkg', 'user')
            gitbaseurl = configp.get('rhcephpkg', 'gitbaseurl')
        except configparser.Error as err:
            raise SystemExit('Problem parsing .rhcephpkg.conf: %s',
                             err.message)
        # TODO: SafeConfigParser might make the "user" interpolation here
        # unnecessary? Need to test, particularly what it does to %(module).
        pkg_url = gitbaseurl % {'user': user, 'module': pkg}
        cmd = ['git', 'clone', pkg_url]
        subprocess.check_call(cmd)
