import re
import subprocess
import six
from tambo import Transport
import rhcephpkg.util as util
from bugzilla import Bugzilla


BZ_REGEX = r'rhbz#(\d+)'


def get_bzapi():
    """ Return a logged-in RHBZ API instance """
    bzapi = Bugzilla('bugzilla.redhat.com')
    if not bzapi.logged_in:
        raise SystemExit('Not logged into BZ')
    return bzapi


def last_commit_message():
    """ Return the last Git commit message's contents.  """
    output = subprocess.check_output(['git', 'show'])
    if six.PY3:
        output = output.decode('utf-8')
    return output


def find_bzs(text):
    """ Return a set of RHBZs in this text.  """
    return set(re.findall(BZ_REGEX, text))


def release_flag(branch):
    """
    Return a Bugzilla release flag for this debian branch.

    :raises: ``ValueError`` if we cannot parse this branch.
    """
    (product, version, distro) = branch.split('-')
    if version.endswith('.0'):
        flagver = version
    else:
        if '.' in version:
            (major, _) = version.split('.')
            flagver = '%s.y' % major
        else:
            # Hack for ceph-2:
            flagver = '%s.y' % version
    flag = '%s-%s' % (product, flagver)
    return flag


class Gitbz(object):
    help_menu = 'verify each RHBZ in the last Git commit message'
    _help = """
Verify that each RHBZ in the last Git commit message is approved for this
release.

If the commit message lacks any RHBZ number, or any RHBZs do not correspond to
this release (dist-git branch), then this command exits with a non-zero exit
code.

Requires a cached login to bugzilla (`bugzilla login` command).

This tool mimics the validation that the internal "gitbz" tool provides for
RHEL dist-git.
"""
    name = 'gitbz'

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
        debian_branch = util.current_debian_branch()
        try:
            flag = release_flag(debian_branch)
        except ValueError:
            raise SystemExit('could not parse debian branch "%s".'
                             % debian_branch)

        msg = last_commit_message()
        bzids = find_bzs(msg)

        if not bzids:
            raise SystemExit('no BZs found')

        bzapi = get_bzapi()
        bugs = bzapi.getbugs(bzids,
                             include_fields=['id', 'flags'],
                             permissive=False)
        missing = []
        for bug in bugs:
            has_release_flag = False
            for f in bug.flags:
                if f['name'] == flag:
                    print('rhbz#%s: %s%s' % (bug.id, f['name'], f['status']))
                    has_release_flag = True
            if not has_release_flag:
                missing.append(bug.id)

        if missing:
            print('Missing %s release flag:' % flag)
            for m in missing:
                print('rhbz#%s' % m)
            raise SystemExit(1)
