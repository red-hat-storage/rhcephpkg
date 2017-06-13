from rhcephpkg import Source
from rhcephpkg.tests.util import CallRecorder


class TestSource(object):

    def test_source(self, monkeypatch):
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        localbuild = Source([])
        localbuild._run()
        expected = ['gbp', 'buildpackage', '--git-tag', '--git-retag',
                    '-S', '-us', '-uc']
        assert recorder.args == expected
