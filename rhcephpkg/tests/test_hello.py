import pytest
from rhcephpkg import Hello
from rhcephpkg.tests.util import CallRecorder


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
        monkeypatch.setattr('jenkins.Jenkins.get_whoami',
                            lambda x: {'fullName': 'Ken'})
        monkeypatch.setattr('jenkins.Jenkins.get_version', lambda x: '1.5')
        hello = Hello([])
        hello._run()
        out, _ = capsys.readouterr()
        assert out == "Hello Ken from Jenkins 1.5\n"
