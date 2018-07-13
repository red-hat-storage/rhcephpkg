import pytest
from rhcephpkg import Source
from rhcephpkg.tests.util import CallRecorder


class TestSource(object):

    def test_help(self, capsys):
        source = Source(['rhcephpkg', 'source', '--help'])
        with pytest.raises(SystemExit):
            source.main()
        out, _ = capsys.readouterr()
        assert "Build a source package on the local system." in out

    def test_source(self, monkeypatch):
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        source = Source([])
        source._run()
        expected = ['gbp', 'buildpackage', '--git-tag', '--git-retag',
                    '-S', '-us', '-uc']
        assert recorder.args == expected
