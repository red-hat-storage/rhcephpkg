import sys
from tambo import Transport
import rhcephpkg


class RHCephPkg(object):
    """ Main class for rhcephpkg CLI. """

    _help = """
Package and build Red Hat Ceph Storage for Ubuntu.

Version: %s

Global Options:
-h, --help, help    Show this program's help menu

%s
"""

    mapper = {
        'build': rhcephpkg.Build,
        'clone': rhcephpkg.Clone,
        'download': rhcephpkg.Download,
        'hello': rhcephpkg.Hello,
        'localbuild': rhcephpkg.Localbuild,
        'source': rhcephpkg.Source,
    }

    def __init__(self, argv=None, parse=True):
        if argv is None:
            argv = sys.argv
        if parse:
            self.main(argv)

    def help(self):
        sub_help = '\n'.join(['%-19s %s' % (
            sub.name, getattr(sub, 'help_menu', ''))
            for sub in self.mapper.values()])
        return self._help % (rhcephpkg.__version__, sub_help)

    def main(self, argv):
        options = []
        parser = Transport(argv, mapper=self.mapper,
                           options=options, check_help=False,
                           check_version=False)
        parser.parse_args()
        parser.catch_help = self.help()
        parser.catch_version = rhcephpkg.__version__
        parser.mapper = self.mapper
        if len(argv) <= 1:
            return parser.print_help()
        parser.dispatch()
        parser.catches_help()
        parser.catches_version()
