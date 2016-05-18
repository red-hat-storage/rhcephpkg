import os
import pytest
from rhcephpkg import util

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestUtilCurrentBranch(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_output(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return "fake-branch\n"

    def test_current_branch(self, monkeypatch):
        monkeypatch.setattr('subprocess.check_output', self.fake_check_output)
        branch = util.current_branch()
        assert self.last_cmd == ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        assert branch == 'fake-branch'


class TestUtilConfig(object):

    def test_missing_config_file(self, monkeypatch, tmpdir):
        # Set $HOME to a known-empty directory:
        monkeypatch.setenv('HOME', str(tmpdir))
        c = util.config()
        with pytest.raises(Exception):
            c.get('some.section', 'someoption')

    def test_working_config_file(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        c = util.config()
        assert c.get('rhcephpkg', 'user') == 'kdreyer'
        assert c.get('rhcephpkg', 'gitbaseurl') == \
            'ssh://%(user)s@git.example.com/ubuntu/%(module)s'
        assert c.get('rhcephpkg.jenkins', 'token') == \
            '5d41402abc4b2a76b9719d911017c592'
        assert c.get('rhcephpkg.jenkins', 'url') == \
            'https://ceph-jenkins.example.com/'
        assert c.get('rhcephpkg.chacra', 'url') == \
            'https://chacra.example.com/'


class TestUtilPackageName(object):

    def test_package_name(self, tmpdir, monkeypatch):
        tmpdir.mkdir('mypkg')
        monkeypatch.chdir(tmpdir.join('mypkg'))
        assert util.package_name() == 'mypkg'
