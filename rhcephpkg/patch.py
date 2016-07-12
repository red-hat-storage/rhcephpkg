import re
import subprocess
import tempfile
from tambo import Transport
import rhcephpkg.log as log
import rhcephpkg.util as util

BZ_REGEX = r'rhbz#(\d+)'


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

        # Switch to "debian" branch
        cmd = ['gbp', 'pq', 'switch']
        subprocess.check_call(cmd)

        # Get the original (old) patch series
        old_series = self.read_series_file('debian/patches/series')
        old_subjects = map(lambda x: x.subject, old_series)

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

        # Get the new patch series
        new_series = self.read_series_file('debian/patches/series')

        # Add patch entries to d/changelog
        changelog = []
        for p in new_series:
            if p.subject in old_subjects:
                continue
            change = p.subject
            bzs = self.get_rhbzs(p)
            bzstr = ' '.join(map(lambda x: 'rhbz#%s' % x, bzs))
            if bzstr != '':
                change += ' (%s)' % bzstr
            changelog.append(change)
        util.bump_changelog(changelog)

        # Assemble a standard commit message string "clog".
        clog = "debian: %s\n" % util.get_deb_version()
        clog += "\n"
        clog += "Add patches from %s\n" % patches_branch
        clog += "\n"
        clog += util.format_changelog(changelog)

        # Commit everything with the standard commit message.
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(clog)
            temp.flush()
            cmd = ['git', 'commit', 'debian/changelog', 'debian/patches',
                   'debian/rules', '-F', temp.name]
            subprocess.check_call(cmd)

    def get_rhbzs(self, patch):
        bzs = re.findall(BZ_REGEX, patch.subject)
        bzs.extend(re.findall(BZ_REGEX, patch.long_desc))
        return bzs

    def read_series_file(self, file_):
        try:
            from gbp.patch_series import PatchSeries
            return PatchSeries.read_series_file(file_)
        except ImportError:
            log.warning('Please run "sudo apt-get install '
                        'git-buildpackage" to write the patches to '
                        './debian/changelog')
