from rhcephpkg import Source


class TestSource(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    def test_source(self, monkeypatch):
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        localbuild = Source([])
        localbuild._run()
        assert self.last_cmd == ['gbp', 'buildpackage', '--git-tag',
                                 '--git-retag', '-S', '-us', '-uc']
