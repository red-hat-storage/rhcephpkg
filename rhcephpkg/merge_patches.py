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

Options:
--force    Do a hard reset, rather than restricting to fast-forward merges
           only. Use this option if the RHEL patches branch was amended or
           rebased for some reason.
"""
    name = 'merge-patches'

    def __init__(self, argv):
        self.argv = argv
        self.options = ['--force', '--hard-reset']

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        force = False
        if self.parser.has(['--force', '--hard-reset']):
            force = True
        if self.parser.unknown_commands:
            log.error('unknown option %s',
                      ' '.join(self.parser.unknown_commands))
            return self.parser.print_help()
        self._run(force)

    def help(self):
        return self._help

    def _run(self, force=False):
        # Determine the names of the relevant branches
        current_branch = util.current_branch()
        debian_branch = util.current_debian_branch()
        patch_queue_branch = util.current_patch_queue_branch()
        rhel_patches_branch = self.get_rhel_patches_branch(debian_branch)

        # Do the merge
        if current_branch == patch_queue_branch:
            # HEAD is our patch-queue branch. Use "git pull" directly.
            # For example: "git pull --ff-only patches/ceph-2-rhel-patches"
            cmd = ['git', 'pull', '--ff-only',
                   'patches/' + rhel_patches_branch]
            if force:
                # Do a hard reset on HEAD instead.
                cmd = ['git', 'reset', '--hard',
                       'patches/' + rhel_patches_branch]
        else:
            # HEAD is our debian branch. Use "git fetch" to update the
            # patch-queue ref. For example:
            # "git fetch . \
            #  patches/ceph-2-rhel-patches:patch-queue/ceph-2-ubuntu"
            util.ensure_patch_queue_branch()
            cmd = ['git', 'fetch', '.',
                   'patches/%s:%s' % (rhel_patches_branch, patch_queue_branch)]
            if force:
                # Do a hard push (with "+") instead.
                cmd = ['git', 'push', '.', '+patches/%s:%s' %
                       (rhel_patches_branch, patch_queue_branch)]
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
        ceph-2-ubuntu-hotfix-bz123 -> ceph-2-rhel-patches-hotfix-bz123
        """
        (product, version, distro) = debian_branch.split('-', 2)
        suffix = None
        if '-' in distro:
            (distro, suffix) = distro.split('-', 1)
        rhel = '%s-%s-rhel-patches' % (product, version)
        if suffix is not None:
            rhel = '%s-%s' % (rhel, suffix)
        return rhel
