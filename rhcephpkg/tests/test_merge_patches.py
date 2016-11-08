import os
import pytest
from rhcephpkg import MergePatches

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestMergePatches(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    def test_merge_patch_on_debian_branch(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        # set current_branch() to a debian branch:
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'ceph-2-ubuntu')
        localbuild = MergePatches(())
        localbuild._run()
        # Verify that we run the "git fetch" command here.
        expected = ['git', 'fetch', '.',
                    'patches/ceph-2-rhel-patches:patch-queue/ceph-2-ubuntu']
        assert self.last_cmd == expected

    def test_merge_patch_on_patch_queue_branch(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        # set current_branch() to a patch-queue branch:
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'patch-queue/ceph-2-ubuntu')
        localbuild = MergePatches(())
        localbuild._run()
        # Verify that we run the "git merge" command here.
        expected = ['git', 'pull', '--ff-only', 'patches/ceph-2-rhel-patches']
        assert self.last_cmd == expected


class TestMergePatchesRhelPatchesBranch(object):

    @pytest.mark.parametrize('debian_branch,expected', [
        ('ceph-1.3-ubuntu', 'ceph-1.3-rhel-patches'),
        ('ceph-2-ubuntu', 'ceph-2-rhel-patches'),
        ('ceph-2-trusty', 'ceph-2-rhel-patches'),
        ('ceph-2-xenial', 'ceph-2-rhel-patches'),
        ('someotherproduct-2-ubuntu', 'someotherproduct-2-rhel-patches'),
    ])
    def test_get_rhel_patches_branch(self, debian_branch, expected):
        m = MergePatches(())
        assert m.get_rhel_patches_branch(debian_branch) == expected
