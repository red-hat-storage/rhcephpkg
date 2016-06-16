import re
import subprocess
from tambo import Transport
# import rhcephpkg.log as log
import rhcephpkg.util as util


class Patch(object):
    help_menu = 'apply patches from patch-queue branch'
    _help = """
Generate patches from a patch-queue branch.

"""
    name = 'patch'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        self._run()

    def help(self):
        return self._help

    def _run(self):
        """ Generate quilt patch series with gbp pq, and update d/rules """

        patches_branch = util.current_branch()
        if not patches_branch.startswith('patch-queue/'):
            raise SystemExit('%s is not a patch-queue branch' % patches_branch)

        # TODO: default to fetching from upstream, the way rdopkg patch does.

        # Get the new sha1 to insert into the $COMMIT variable in d/rules
        cmd = ['git', 'rev-parse', patches_branch]
        patches_sha1 = subprocess.check_output(cmd).rstrip()

        # Git-buildpackage pq operation
        cmd = ['gbp', 'pq', 'export']
        subprocess.check_call(cmd)

        # Add all patch files to Git's index
        cmd = ['git', 'add', '--all', 'debian/patches']
        subprocess.check_call(cmd)

        # Replace $COMMIT sha1 in d/rules
        with open('debian/rules') as rules:
            rules_file = rules.read()
        old = r'export COMMIT=[0-9a-f]{40}'
        new = 'export COMMIT=%s' % patches_sha1
        with open('debian/rules', 'w') as fileh:
            fileh.write(re.sub(old, new, rules_file))

        # TODO: add patch entries to d/changelog

        # TODO: commit everything with a standard commit message
        # cmd = ['git', 'commit', 'debian/changelog', 'debian/patches',
        #        'debian/rules', '-m', 'add patches from %s' % patches_branch]
        # subprocess.check_call(cmd)
