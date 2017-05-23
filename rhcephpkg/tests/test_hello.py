from rhcephpkg import Hello
from rhcephpkg.tests.util import fake_urlopen


class TestHelloJenkins(object):

    def test_success(self, monkeypatch, capsys):
        # python-jenkins uses a "from" import, "from X import Y", so
        # monkeypatching is trickier.
        monkeypatch.setattr('jenkins.urlopen', fake_urlopen)
        # Another option would be to use func_code. This globally patches all
        # calls to urlopen(), not just jenkins' calls.
        # monkeypatch.setattr('six.moves.urllib.request.urlopen.func_code',
        #                     fake_urlopen.func_code)
        hello = Hello(())
        hello._run()
        out, _ = capsys.readouterr()
        assert out == "Hello Ken from Jenkins 1.5\n"
