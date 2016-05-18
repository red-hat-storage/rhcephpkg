import os
import pytest
from rhcephpkg import Localbuild

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestLocalbuild(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    def test_trusty_localbuild(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        monkeypatch.setattr('rhcephpkg.Localbuild._get_j_arg',
                            lambda *a: '-j2')
        localbuild = Localbuild(())
        localbuild._run('trusty')
        assert self.last_cmd == ['gbp', 'buildpackage', '--git-dist=trusty',
                                 '--git-arch=amd64', '--git-verbose',
                                 '--git-pbuilder', '-j2', '-us', '-uc']


class TestGetJArg(object):
    """ Test private _get_j_arg() function """

    @pytest.mark.parametrize('cpus,ram,expected', [
        (2, 2,  '-j1'),
        (2, 8,  '-j2'),
        (2, 16, '-j2'),
        (2, 32, '-j2'),
        (4, 8,  '-j2'),
        (4, 16, '-j4'),
        (4, 32, '-j4'),
        (8, 8,  '-j2'),
        (8, 16, '-j4'),
        (8, 32, '-j8'),
    ])
    def test_get_j_arg(self, cpus, ram, expected, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        localbuild = Localbuild(())
        result = localbuild._get_j_arg(cpus=cpus, total_ram_gb=ram)
        assert result == expected
