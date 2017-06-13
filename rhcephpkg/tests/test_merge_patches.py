import pytest
import subprocess
from rhcephpkg import MergePatches
from rhcephpkg.tests.util import CallRecorder


def git(*args):
    """ shortcut for shelling out to git """
    cmd = ['git'] + list(args)
    subprocess.check_call(cmd)


class TestMergePatches(object):

    def test_on_debian_branch(self, testpkg, monkeypatch):
        # set our current branch to be a debian branch:
        git('checkout', 'ceph-2-ubuntu')
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        localbuild = MergePatches([])
        localbuild._run()
        # Verify that we run the "git fetch" command here.
        expected = ['git', 'fetch', '.',
                    'patches/ceph-2-rhel-patches:patch-queue/ceph-2-ubuntu']
        assert recorder.args == expected

    def test_on_patch_queue_branch(self, testpkg, monkeypatch):
        # set our current branch to be a patch-queue branch:
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        localbuild = MergePatches([])
        localbuild._run()
        # Verify that we run the "git merge" command here.
        expected = ['git', 'pull', '--ff-only', 'patches/ceph-2-rhel-patches']
        assert recorder.args == expected

    def test_force_on_debian_branch(self, testpkg, monkeypatch):
        # set current_branch() to a debian branch:
        git('checkout', 'ceph-2-ubuntu')
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        localbuild = MergePatches([])
        localbuild._run(force=True)
        # Verify that we run the "git push" command here.
        expected = ['git', 'push', '.',
                    '+patches/ceph-2-rhel-patches:patch-queue/ceph-2-ubuntu']
        assert recorder.args == expected

    def test_force_on_patch_queue_branch(self, testpkg, monkeypatch):
        # set current_branch() to a patch-queue branch:
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        localbuild = MergePatches([])
        localbuild._run(force=True)
        # Verify that we run the "git reset" command here.
        expected = ['git', 'reset', '--hard', 'patches/ceph-2-rhel-patches']
        assert recorder.args == expected


class TestMergePatchesRhelPatchesBranch(object):

    @pytest.mark.parametrize('debian_branch,expected', [
        ('ceph-1.3-ubuntu', 'ceph-1.3-rhel-patches'),
        ('ceph-2-ubuntu', 'ceph-2-rhel-patches'),
        ('ceph-2-trusty', 'ceph-2-rhel-patches'),
        ('ceph-2-xenial', 'ceph-2-rhel-patches'),
        ('someotherproduct-2-ubuntu', 'someotherproduct-2-rhel-patches'),
        ('ceph-2-ubuntu-hotfix-bz123', 'ceph-2-rhel-patches-hotfix-bz123'),
        ('ceph-2-ubuntu-test-bz456', 'ceph-2-rhel-patches-test-bz456'),
    ])
    def test_get_rhel_patches_branch(self, debian_branch, expected):
        m = MergePatches([])
        assert m.get_rhel_patches_branch(debian_branch) == expected
