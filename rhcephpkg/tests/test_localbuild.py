import pytest
from rhcephpkg import Localbuild


class TestLocalbuild(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    @pytest.mark.parametrize('args,expected', [
        (('localbuild'), '--git-dist=trusty'),
        (('localbuild', '--dist', 'trusty'), '--git-dist=trusty'),
        (('localbuild', '--dist', 'xenial'), '--git-dist=xenial'),
    ])
    def test_localbuild(self, args, expected, monkeypatch):
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        monkeypatch.setattr('rhcephpkg.Localbuild._get_j_arg',
                            lambda *a: '-j2')
        localbuild = Localbuild(args)
        localbuild.main()
        assert self.last_cmd == ['gbp', 'buildpackage', expected,
                                 '--git-arch=amd64', '--git-verbose',
                                 '--git-pbuilder', '-j2', '-us', '-uc']

    def test_missing_arg(self, monkeypatch):
        localbuild = Localbuild(('localbuild', '--dist'))
        with pytest.raises(SystemExit) as e:
            localbuild.main()
        assert 'Specify a distro to --dist' in str(e.value)


class TestGetJArg(object):
    """ Test private _get_j_arg() function """

    @pytest.mark.parametrize('cpus,ram,expected', [
        (2, 2, '-j1'),
        (2, 8, '-j2'),
        (2, 16, '-j2'),
        (2, 32, '-j2'),
        (4, 8, '-j2'),
        (4, 16, '-j4'),
        (4, 32, '-j4'),
        (8, 8, '-j2'),
        (8, 16, '-j4'),
        (8, 32, '-j8'),
    ])
    def test_get_j_arg(self, cpus, ram, expected, monkeypatch):
        localbuild = Localbuild(())
        result = localbuild._get_j_arg(cpus=cpus, total_ram_gb=ram)
        assert result == expected
