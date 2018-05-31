import subprocess
import tempfile
from gbp.config import GbpOptionParser
from gbp.deb.git import DebianGitRepository
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
        # Ensure we're on the right branch.
        current_branch = util.current_branch()
        debian_branch = util.current_debian_branch()
        if current_branch != debian_branch:
            log.error('current branch is "%s"' % current_branch)
            log.error('debian branch is "%s"' % debian_branch)
            raise RuntimeError('Must run `new-version` on debian branch')

        util.setup_pristine_tar_branch()
        self.ensure_gbp_settings()

        self.setup_upstream_branch()
        self.import_orig(tarball)
        version = self.upstream_version()
        self.run_dch(version, bugstr)

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

    def upstream_version(self):
        """
        Find the upstream version we just imported.

        git-buildpackage import-orig will generate this "upstream" tag
        automatically, and we can use it to discover the version of the
        current branch. It uses git-describe, like so:

          git describe --match 'upstream/*' --abbrev=0

        (Note: this method is similar to gbp.deb.git.DebianGitRepository
        debian_version_from_upstream(), but that appends the debian
        release number "-1", and we don't want that here.)
        """
        repo = DebianGitRepository('.')
        tag = repo.find_branch_tag('HEAD', 'HEAD', pattern='upstream/*')
        # should we get tagformat from GbpOptionParser instead of hardcoding?
        tagformat = "upstream/%(version)s"
        return repo.tag_to_version(tag, tagformat)

    def run_dch(self, version, bugstr):
        """ Edit debian/changelog for a new upstream release """
        version_release = version + '-2redhat1'
        text = 'Imported Upstream version %s' % version
        if bugstr:
            text = '%s (%s)' % (text, bugstr)
        dist = changelog.distribution()  # reuse previous distribution
        cmd = ['dch', '-D', dist, '-v', version_release, text]
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

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
