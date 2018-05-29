import subprocess
import tempfile
from gbp.config import GbpOptionParser
from tambo import Transport
import rhcephpkg.util as util
import rhcephpkg.log as log
import rhcephpkg.changelog as changelog


class NewVersion(object):
    help_menu = 'Import a new version with git-buildpackage and uscan'
    _help = """
Import a new upstream version with "gbp import-orig --uscan".

This command makes it easier to rebase a package to a new upstream version.

Note: the package must use pristine-tar.

Optional Arguments:

[tarball]  The upstream tarball to import. Omit this to use uscan
           (debian/watch file) instead.

 Example:

  rhcephpkg new-version ansible_2.4.1.0.orig.tar.gz

 This will import the upstream ansible 2.4.1.0 tarball.

-B, --bug  The BZ(s) that this new version resolves.

 Example:

  rhcephpkg new-version -B "rhbz#12345 rhbz#67980"

 This will add rhbz#12345 and rhbz#67890 to the debian/changelog.
"""
    name = 'new-version'

    def __init__(self, argv):
        self.argv = argv
        self.options = [['-B', '--bug']]

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            tarball = self.parser.unknown_commands[0]
        except IndexError:
            tarball = None
        bugstr = self.parser.get('--bug')
        self._run(tarball, bugstr)

    def help(self):
        return self._help

    def _run(self, tarball, bugstr):
        util.setup_pristine_tar_branch()
        self.ensure_gbp_settings()

        self.setup_upstream_branch()
        self.import_orig(tarball)
        self.run_dch()
        self.insert_rhbzs(bugstr)

        # Edit debian/changelog and change the release from gbp-dch's -1
        # to -2redhat1.
        changelog.replace_release('2redhat1')

        self.commit()
        self.show()

    def ensure_gbp_settings(self):
        """ Ensure some gbp settings are correct. """
        parser = GbpOptionParser('import-orig')
        if parser.config.get('pristine-tar') != 'True':
            err = '"pristine-tar" is %s. Set to "True" in debian/gbp.conf.'
            raise RuntimeError(err % parser.config.get('pristine-tar'))
        if parser.config.get('merge-mode') != 'replace':
            err = '"merge-mode" is %s. Set to "replace" in debian/gbp.conf.'
            raise RuntimeError(err % parser.config.get('merge-mode'))
        # ensure upstream branch is unique for this debian branch
        debian_branch = parser.config.get('debian-branch')
        upstream_branch = parser.config.get('upstream-branch')
        expected = 'upstream/%s' % debian_branch
        if upstream_branch != expected:
            err = '"upstream-branch" is "%s". Set to "%s" in debian/gbp.conf.'
            raise RuntimeError(err % (upstream_branch, expected))

    def setup_upstream_branch(self):
        """ Ensure we have a local "upstream/foo" branch. """
        parser = GbpOptionParser('import-orig')
        upstream_branch = parser.config.get('upstream-branch')
        util.ensure_local_branch(upstream_branch)

    def import_orig(self, tarball=None):
        """ Import new upstream tarball, optionally with uscan. """
        cmd = ['gbp', 'import-orig', '--no-interactive']
        if tarball is None:
            cmd.append('--uscan')
        else:
            cmd.append(tarball)
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

    def run_dch(self):
        """ Bump debian/changelog for a new release """
        cmd = ['gbp', 'dch', '--auto', '-R', '--spawn-editor=never']
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

    def insert_rhbzs(self, bugstr):
        """
        Edit debian/changelog in place and add any RHBZ numbers.

        :param bzs: string
        """
        if not bugstr:
            return
        changes = changelog.list_changes()
        if len(changes) > 1:
            # defensively verify that dch only inserted one entry.
            raise RuntimeError('unexpected entries in d/changelog')
        changes[0] = '%s (%s)' % (changes[0], bugstr)
        changelog.replace_changes(changes)

    def commit(self):
        """
        Commit to Git, basing the message on our debian/changelog.
        """
        message = changelog.git_commit_message()
        with tempfile.NamedTemporaryFile(mode='w+') as temp:
            temp.write(message)
            temp.flush()
            cmd = ['git', 'commit', 'debian/changelog', '-F', temp.name]
            subprocess.check_call(cmd)

    def show(self):
        """
        Show our last Git commit.
        """
        subprocess.check_call(['git', 'show'])
