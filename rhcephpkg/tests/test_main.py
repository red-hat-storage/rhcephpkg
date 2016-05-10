import json
import os
import pytest
import re

import httpretty
try:
    from jenkins import CRUMB_URL
except ImportError:
    # CRUMB_URL was introduced in python-jenkins v0.2.2
    CRUMB_URL = 'crumbIssuer/api/json'

from rhcephpkg.main import RHCephPkg

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestConfigFile(object):

    def test_missing_config_file(self, monkeypatch, tmpdir):
        # Set $HOME to a known-empty directory:
        monkeypatch.setenv('HOME', str(tmpdir))
        with pytest.raises(SystemExit):
            RHCephPkg()

    def test_working_config_file(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        expected_config = {
            'user': 'kdreyer',
            'gitbaseurl': 'ssh://%(user)s@git.example.com/ubuntu/%(module)s',
            'jenkins_token': '5d41402abc4b2a76b9719d911017c592',
            'jenkins_url': 'https://ceph-jenkins.example.com/',
            'chacra_url': 'https://chacra.example.com/',
        }
        rhcpkg = RHCephPkg()
        assert rhcpkg.config == expected_config


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
        rhcpkg = RHCephPkg()
        result = rhcpkg._get_j_arg(cpus=cpus, total_ram_gb=ram)
        assert result == expected


class TestHelloJenkins(object):

    @classmethod
    def setup_class(cls):
        httpretty.enable()
        httpretty.HTTPretty.allow_net_connect = False

    @classmethod
    def teardown_class(cls):
        httpretty.disable()

    def test_success(self, monkeypatch, capsys):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        # "Who Am I" endpoint.
        httpretty.register_uri(httpretty.GET,
                               'https://ceph-jenkins.example.com/me/api/json',
                               body='{"fullName": "Ken"}',
                               content_type='text/json')
        # python-jenkins v0.2.2+ checks this CRUMB_URL in its
        # maybe_add_crumb(). Return a 404 so python-jenkins catches the
        # NotFoundException and carries on.
        httpretty.register_uri(httpretty.GET,
                               'https://ceph-jenkins.example.com/' + CRUMB_URL,
                               status=404)
        # "Jenkins Version" endpoint.
        httpretty.register_uri(httpretty.GET,
                               'https://ceph-jenkins.example.com/',
                               adding_headers={'X-Jenkins': '1.5'})
        rhcpkg = RHCephPkg()
        rhcpkg.hello_jenkins()
        out, _ = capsys.readouterr()
        assert out == "Hello Ken from Jenkins 1.5\n"


class TestClone(object):

    def setup_method(self, method):
        """ Reset last_cmd before each test. """
        self.last_cmd = None

    def fake_check_call(self, cmd):
        """ Store cmd, in order to verify it later. """
        self.last_cmd = cmd
        return 0

    def test_basic_clone(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('sys.argv', ['rhcephpkg', 'clone', 'mypkg'])
        monkeypatch.setattr('subprocess.check_call', self.fake_check_call)
        rhcpkg = RHCephPkg()
        rhcpkg.clone()
        assert self.last_cmd == ['git', 'clone',
                                 'ssh://kdreyer@git.example.com/ubuntu/mypkg']


class TestDownload(object):

    @classmethod
    def setup_class(cls):
        httpretty.enable()
        httpretty.HTTPretty.allow_net_connect = False

    @classmethod
    def teardown_class(cls):
        httpretty.disable()

    def test_basic_download(self, monkeypatch, tmpdir):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        fake_args = ['rhcephpkg', 'download', 'ceph_10.2.0-2redhat1trusty']
        # Fake build API endpoint.
        url = 'https://chacra.example.com' \
              '/binaries/ceph/10.2.0-2redhat1trusty/ubuntu/all'
        # Fake JSON payload for the build API endpoint above.
        payload = {'source': ['ceph_10.2.0-2redhat1trusty.debian.tar.gz',
                              'ceph_10.2.0-2redhat1trusty.dsc',
                              'ceph_10.2.0-2redhat1trusty_amd64.changes',
                              'ceph_10.2.0.orig.tar.gz'],
                   'amd64': ['libcephfs1-dbg_10.2.0-2redhat1trusty_amd64.deb',
                             'librbd-dbg_10.2.0-2redhat1trusty_amd64.deb',
                             'ceph_10.2.0-2redhat1trusty_amd64.deb',
                             'radosgw_10.2.0-2redhat1trusty_amd64.deb'],
                   'noarch': ['libcephfs-java_10.2.0-2redhat1trusty_all.deb'],
                   }

        httpretty.register_uri(httpretty.GET,
                               url,
                               body=json.dumps(payload),
                               content_type='text/json')
        httpretty.register_uri(httpretty.GET,
                               re.compile('^%s/.+' % url),
                               body='(fake binary file contents)',
                               content_type='application/octet-stream')
        monkeypatch.setattr('sys.argv', fake_args)
        monkeypatch.chdir(tmpdir)
        RHCephPkg()
        for binaries in payload.values():
            for binary in binaries:
                assert os.path.isfile(binary)
