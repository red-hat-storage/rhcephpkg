import re
import subprocess
from tambo import Transport
import rhcephpkg.util as util
import rhcephpkg.log as log


class MergePatches(object):
    help_menu = 'Merge patches from RHEL -patches branch to patch-queue branch'
    _help = """
Fetch the latest patches branch that rdopkg uses, and then fast-forward merge
that into our local patch-queue branch, so that both branches align.

This command helps to align the patch series between our RHEL packages and our
Ubuntu packages.

"""
    name = 'merge-patches'

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
        # Determine the names of the relevant branches
        current_branch = util.current_branch()
        debian_branch = util.current_debian_branch()
        patches_branch = util.current_patches_branch()
        rhel_patches_branch = self.get_rhel_patches_branch(debian_branch)

        # Do the merge
        if current_branch == patches_branch:
            # HEAD is our patch-queue branch. Use "git pull" directly.
            # For example: "git pull --ff-only patches/ceph-2-rhel-patches"
            cmd = ['git', 'pull', '--ff-only',
                   'patches/' + rhel_patches_branch]
        else:
            # HEAD is our debian branch. Use "git fetch" to update the
            # patch-queue ref. For example:
            # "git fetch . \
            #  patches/ceph-2-rhel-patches:patch-queue/ceph-2-ubuntu"
            cmd = ['git', 'fetch', '.',
                   'patches/%s:%s' % (rhel_patches_branch, patches_branch)]
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

    def get_rhel_patches_branch(self, debian_branch):
        """
        Get the RHEL -patches branch corresponding to this debian branch.

        Examples:
        ceph-2-ubuntu -> ceph-2-rhel-patches
        ceph-2-trusty -> ceph-2-rhel-patches
        ceph-2-xenial -> ceph-2-rhel-patches
        ceph-1.3-ubuntu -> ceph-1.3-rhel-patches
        """
        deb_regex = r'^(\w+)-([\d\.]+)-.*'
        rhel_regex = r'\1-\2-rhel-patches'
        return re.sub(deb_regex, rhel_regex, debian_branch)
