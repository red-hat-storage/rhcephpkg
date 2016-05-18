import os
import pytest
from rhcephpkg import Clone

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestClone(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    def test_basic_clone(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        clone = Clone(())
        clone._run('mypkg')
        assert self.last_cmd == ['git', 'clone',
                                 'ssh://kdreyer@git.example.com/ubuntu/mypkg']

    def test_already_exists(self, tmpdir, monkeypatch):
        tmpdir.mkdir('mypkg')
        monkeypatch.chdir(tmpdir)
        clone = Clone(())
        with pytest.raises(SystemExit):
            clone._run('mypkg')
