import pytest
from rhcephpkg import Hello
from rhcephpkg.tests.util import fake_urlopen, CallRecorder


class TestHelloJenkins(object):

    def test_main(self, monkeypatch):
        recorder = CallRecorder()
        monkeypatch.setattr(Hello, '_run', recorder)
        hello = Hello([])
        hello.main()
        assert recorder.called

    def test_help(self, capsys):
        hello = Hello(['rhcephpkg', 'hello', '--help'])
        with pytest.raises(SystemExit):
            hello.main()
        out, _ = capsys.readouterr()
        assert "Test authentication to Jenkins" in out

    def test_success(self, monkeypatch, capsys):
        # python-jenkins uses a "from" import, "from X import Y", so
        # monkeypatching is trickier.
        monkeypatch.setattr('jenkins.urlopen', fake_urlopen)
        monkeypatch.setattr('rhcephpkg.jenkins.urlopen', fake_urlopen)
        # Another option would be to use func_code. This globally patches all
        # calls to urlopen(), not just jenkins' calls.
        # monkeypatch.setattr('six.moves.urllib.request.urlopen.func_code',
        #                     fake_urlopen.func_code)
        hello = Hello([])
        hello._run()
        out, _ = capsys.readouterr()
        assert out == "Hello Ken from Jenkins 1.5\n"

    def test_old_jenkins(self, monkeypatch, capsys):
        """ Repeat the above test, but without the "new" get_version() API. """
        monkeypatch.delattr('jenkins.Jenkins.get_version', raising=False)
        monkeypatch.setattr('rhcephpkg.hello.urlopen', fake_urlopen)
        self.test_success(monkeypatch, capsys)
