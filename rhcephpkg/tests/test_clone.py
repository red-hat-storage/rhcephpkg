import os
import pytest
from rhcephpkg import Clone


class TestClone(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_git_clone(self, *args):
        """ Just make a directory in cwd. """
        try:
            dirname = args[1]
        except IndexError:
            dirname = os.path.basename(args[0])
        os.mkdir(dirname)

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        if cmd[:2] == ['git', 'clone']:
            self.fake_git_clone(*cmd[2:])
        self.last_cmd = cmd
        return 0

    def test_basic_clone(self, tmpdir, monkeypatch):
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        monkeypatch.chdir(tmpdir)
        clone = Clone(())
        clone._run('mypkg')
        assert self.last_cmd == ['git', 'clone',
                                 'ssh://kdreyer@git.example.com/ubuntu/mypkg']

    def test_already_exists(self, tmpdir, monkeypatch):
        tmpdir.mkdir('mypkg')
        monkeypatch.chdir(tmpdir)
        clone = Clone(())
        with pytest.raises(SystemExit) as e:
            clone._run('mypkg')
        expected = 'mypkg already exists in current working directory.'
        assert str(e.value) == expected
