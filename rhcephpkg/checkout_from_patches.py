import re
import subprocess
import six
from tambo import Transport
import rhcephpkg.log as log


class CheckoutFromPatches(object):
    help_menu = 'Choose a Debian branch based on a RHEL -patches branch'
    _help = """
Check out the Git branch that corresponds to a given RHEL (rdopkg-style)
-patches branch.

If you are starting from a RHEL -patches branch name (say, from a trigger in
Jenkins), this will automatically choose the right Debian branch that goes
with your -patches branch.

Example:

  rhcephpkg checkout-from-patches ceph-3.0-rhel-patches

... this will checkout the "ceph-3.0-xenial" Git branch if it exists in the
"origin" remote, or fall back to the "ceph-3.0-ubuntu" branch, or error if
neither exist.

Positional Arguments:

[branch]  The name of the -patches branch.
"""
    name = 'checkout-from-patches'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            patches_branch = self.parser.unknown_commands[0]
        except IndexError:
            return self.parser.print_help()
        self._run(patches_branch)

    def help(self):
        return self._help

    def _run(self, patches_branch):
        debian_branch = self.get_debian_branch(patches_branch)
        if not debian_branch:
            err = 'could not find debian branch for %s' % patches_branch
            raise SystemExit(err)

        cmd = ['git', 'checkout', debian_branch]
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

    def get_debian_branch(self, patches_branch):
        """
        Get the debian branch corresponding to this RHEL -patches branch.

        Examples:
        ceph-2-rhel-patches -> ceph-2-xenial or ceph-2-ubuntu
        ceph-2-rhel-patches-hotfix-bz123 -> ceph-2-ubuntu-hotfix-bz123

        :returns: name of debian branch, or None if none was found.
        """
        patches_re = re.compile('-rhel-patches')
        debian_re = patches_re.sub('-([a-z]+)', patches_branch)
        ubuntu_branch = None
        for branch in self.get_origin_branches():
            m = re.match('^%s$' % debian_re, branch)
            if m:
                if m.group(1) == 'ubuntu':
                    # Use this only if we could find no other distro branch.
                    ubuntu_branch = branch
                else:
                    return branch
        return ubuntu_branch

    def get_origin_branches(self):
        """ Return a list of all the branches in the "origin" remote. """
        cmd = ['git', 'branch', '-r', '--list', 'origin/*']
        output = subprocess.check_output(cmd)
        if six.PY3:
            output = output.decode('utf-8')
        lines = output.split("\n")
        branches = [line.strip()[7:] for line in lines]
        return branches
