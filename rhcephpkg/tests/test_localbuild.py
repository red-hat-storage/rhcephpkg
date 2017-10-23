import os
import re
import pytest
from rhcephpkg import Localbuild
from rhcephpkg.localbuild import setup_pbuilder_cache
from rhcephpkg.localbuild import get_distro
from rhcephpkg.tests.util import CallRecorder


class TestLocalbuild(object):
    @pytest.mark.parametrize('args,expected', [
        (['localbuild'], '--git-dist=xenial'),
        (['localbuild', '--dist', 'trusty'], '--git-dist=trusty'),
        (['localbuild', '--dist', 'xenial'], '--git-dist=xenial'),
    ])
    def test_localbuild(self, testpkg, args, expected, monkeypatch):
        recorder = CallRecorder()
        monkeypatch.setattr('subprocess.check_call', recorder)
        monkeypatch.setattr('rhcephpkg.Localbuild._get_j_arg',
                            lambda *a: '-j2')
        localbuild = Localbuild(args)
        localbuild.main()
        assert recorder.args == ['gbp', 'buildpackage', expected,
                                 '--git-arch=amd64', '--git-verbose',
                                 '--git-pbuilder', '-j2', '-us', '-uc']

    def test_missing_arg(self):
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
    def test_get_j_arg(self, cpus, ram, expected):
        localbuild = Localbuild([])
        result = localbuild._get_j_arg(cpus=cpus, total_ram_gb=ram)
        assert result == expected

    def test_get_j_arg_live(self):
        localbuild = Localbuild([])
        # Rather than calculating the amount of RAM on this system and
        # basically re-implementing the entire code here to get the exact
        # expected result, just pattern-match for basic sanity.
        result = localbuild._get_j_arg(cpus=1)
        assert re.match('-j\d+$', result)


class TestSetupPbuilderCache(object):

    def setup_method(self, method):
        """ Reset cmds before each test. """
        self.cmds = []

    def fake_sudo_rm(self, cmd):
        """ Fake "sudo rm <foo>" command. """
        for filename in cmd[2:]:
            if os.path.exists(filename):
                os.remove(filename)

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.cmds.append(cmd)
        # and fake "sudo rm"...
        if cmd[0] == 'sudo' and cmd[1] == 'rm':
            self.fake_sudo_rm(cmd)
        return 0

    @pytest.fixture(autouse=True)
    def patch_subprocess(self, monkeypatch):
        """ Monkeypatch subprocess for each test. """
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)

    @pytest.fixture
    def tmpcache(self, tmpdir):
        """ Fake pbuilder cache file in a tmpdir. """
        cache = tmpdir.join('base-trusty-amd64.tgz')
        cache.write('testcachedata')
        return cache

    def test_exists(self, tmpcache):
        pbuilder_cache = str(tmpcache)
        setup_pbuilder_cache(pbuilder_cache, 'trusty')
        assert self.cmds == []

    def test_no_exist(self):
        pbuilder_cache = '/noexist/base-trusty-amd64.tgz'
        setup_pbuilder_cache(pbuilder_cache, 'trusty')
        expected = ['sudo', 'pbuilder', 'create', '--debootstrapopts',
                    '--variant=buildd', '--basetgz', pbuilder_cache,
                    '--distribution', 'trusty']
        assert self.cmds == [expected]

    def test_zero_length(self, tmpcache):
        tmpcache.write('')
        pbuilder_cache = str(tmpcache)
        setup_pbuilder_cache(pbuilder_cache, 'trusty')
        rm = ['sudo', 'rm', pbuilder_cache]
        create = ['sudo', 'pbuilder', 'create', '--debootstrapopts',
                  '--variant=buildd', '--basetgz', pbuilder_cache,
                  '--distribution', 'trusty']
        assert self.cmds == [rm, create]


class TestGetDistro(object):

    @pytest.mark.parametrize('branch,expected', [
        ('ceph-1.3-ubuntu', 'trusty'),
        ('ceph-1.3-trusty', 'trusty'),
        ('ceph-2-ubuntu', 'xenial'),
        ('ceph-2-trusty', 'trusty'),
        ('ceph-2-xenial', 'xenial'),
        ('ceph-3.0-ubuntu', 'xenial'),
        ('private-kdreyer-ceph-1.3-ubuntu', 'trusty'),
        ('private-kdreyer-ceph-3.0-ubuntu', 'xenial'),
    ])
    def test_branch_name(self, monkeypatch, branch, expected):
        monkeypatch.setattr('rhcephpkg.util.current_branch', lambda: branch)
        assert get_distro() == expected

    def test_bad_branch_name(self, monkeypatch):
        branch = 'bad-branch'
        monkeypatch.setattr('rhcephpkg.util.current_branch', lambda: branch)
        with pytest.raises(IndexError):
            assert get_distro()

    def test_too_new_branch_name(self, monkeypatch):
        branch = 'ceph-4.0-ubuntu'
        monkeypatch.setattr('rhcephpkg.util.current_branch', lambda: branch)
        with pytest.raises(NotImplementedError):
            assert get_distro()
