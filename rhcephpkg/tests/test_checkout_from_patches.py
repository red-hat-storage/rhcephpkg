import os
import subprocess
import six
import pytest
from rhcephpkg.checkout_from_patches import CheckoutFromPatches
from rhcephpkg.tests.util import CallRecorder


class TestCheckoutFromPatches(object):

    @pytest.fixture
    def testpkg(self, testpkg):
        """
        Override the testpkg fixture with remote refs.
        """
        origin = testpkg.join('.git/refs/remotes/origin')
        output = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        sha = output.rstrip()
        if six.PY3:
            sha = output.decode('utf-8').rstrip()
        branches = ['ceph-2-xenial',
                    'ceph-3.0-ubuntu',
                    'ceph-2-ubuntu-hotfix-bz123',
                    'private-kdreyer-ceph-2-ubuntu-test-bz456']
        os.makedirs(str(origin))
        for branch in branches:
            origin.join(branch).write(sha)
        return testpkg

    @pytest.mark.parametrize('patches_branch,expected', [
        ('ceph-2-rhel-patches', 'ceph-2-xenial'),
        ('ceph-3.0-rhel-patches', 'ceph-3.0-ubuntu'),
        ('ceph-2-rhel-patches-hotfix-bz123', 'ceph-2-ubuntu-hotfix-bz123'),
        ('private-kdreyer-ceph-2-rhel-patches-test-bz456',
         'private-kdreyer-ceph-2-ubuntu-test-bz456'),
        ('ceph-4.0-rhel-patches', None),
    ])
    def test_get_debian_branch(self, testpkg, patches_branch, expected):
        cfp = CheckoutFromPatches(['checkout-from-patches', patches_branch])
        result = cfp.get_debian_branch(patches_branch)
        assert result == expected

    def test_no_args(self, testpkg, capsys):
        cfp = CheckoutFromPatches(['checkout-from-patches'])
        with pytest.raises(SystemExit):
            cfp.main()
        out, _ = capsys.readouterr()
        assert cfp._help in out

    def test_help(self, testpkg, capsys):
        cfp = CheckoutFromPatches(['checkout-from-patches', '--help'])
        with pytest.raises(SystemExit):
            cfp.main()
        out, _ = capsys.readouterr()
        assert cfp._help in out

    def test_checkout(self, testpkg, monkeypatch):
        """ Test the happy path for checking out a branch """
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        argv = ['checkout-from-patches', 'ceph-2-rhel-patches']
        cfp = CheckoutFromPatches(argv)
        cfp.main()
        assert recorder.args == ['git', 'checkout', 'ceph-2-xenial']

    def test_bad_checkout(self, testpkg):
        """ Test a branch that doesn't exist """
        argv = ['checkout-from-patches', 'ceph-4.0-rhel-patches']
        cfp = CheckoutFromPatches(argv)
        with pytest.raises(SystemExit) as e:
            cfp.main()
        expected = 'could not find debian branch for ceph-4.0-rhel-patches'
        assert str(e.value) == expected
