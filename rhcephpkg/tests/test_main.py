import sys
import pytest
import rhcephpkg
from rhcephpkg.main import RHCephPkg


class TestMain(object):

    def capture_out(self, capsys):
        with pytest.raises(SystemExit):
            RHCephPkg()
        out, _ = capsys.readouterr()
        return out

    def test_no_args(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, 'argv', ['rhcephpkg'])
        out = self.capture_out(capsys)
        assert "Package and build Red Hat Ceph Storage for Ubuntu" in out

    def test_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, 'argv', ['rhcephpkg', '--help'])
        out = self.capture_out(capsys)
        assert "Package and build Red Hat Ceph Storage for Ubuntu" in out

    def test_version(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, 'argv', ['rhcephpkg', '--version'])
        with pytest.raises(SystemExit):
            RHCephPkg()
        out, _ = capsys.readouterr()
        expected = "%s\n" % rhcephpkg.__version__
        assert out == expected
