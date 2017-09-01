import os
import pytest
from rhcephpkg import Clone
from rhcephpkg.tests.util import CallRecorder


class CheckCallRecorder(CallRecorder):

    def __call__(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.called += 1
        if cmd[:2] == ['git', 'clone']:
            self.fake_git_clone(*cmd[2:])
        self.args = cmd
        return 0

    def fake_git_clone(self, *args):
        """ Just make a directory in cwd. """
        try:
            dirname = args[1]
        except IndexError:
            dirname = os.path.basename(args[0])
        os.mkdir(dirname)


class TestClone(object):

    def test_no_args(self, capsys):
        clone = Clone(['rhcephpkg'])
        with pytest.raises(SystemExit):
            clone.main()
        out, _ = capsys.readouterr()
        expected = clone._help + "\n"
        assert out == expected

    def test_basic_clone(self, tmpdir, monkeypatch):
        recorder = CheckCallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        monkeypatch.chdir(tmpdir)
        clone = Clone(['rhcephpkg', 'mypkg'])
        clone.main()
        assert recorder.args == ['git', 'clone',
                                 'ssh://kdreyer@git.example.com/ubuntu/mypkg']
        assert tmpdir.join('mypkg').check(dir=1)

    def test_already_exists(self, tmpdir, monkeypatch):
        tmpdir.mkdir('mypkg')
        monkeypatch.chdir(tmpdir)
        clone = Clone(['rhcephpkg', 'mypkg'])
        with pytest.raises(SystemExit) as e:
            clone.main()
        expected = 'mypkg already exists in current working directory.'
        assert str(e.value) == expected

    def test_python_package(self, tmpdir, monkeypatch):
        recorder = CheckCallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        monkeypatch.chdir(tmpdir)
        clone = Clone(['rhcephpkg', 'python-apipkg'])
        clone.main()
        assert recorder.args == ['git', 'clone',
                                 'ssh://kdreyer@git.example.com/ubuntu/apipkg']
        assert tmpdir.join('apipkg').check(dir=1)
