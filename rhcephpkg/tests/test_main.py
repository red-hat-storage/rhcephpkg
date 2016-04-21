import os
import pytest

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
        }
        rhcpkg = RHCephPkg()
        assert rhcpkg.config == expected_config


class TestGetNumCpus(object):
    """ Test private _get_num_cpus() function """

    def test_get_num_cpus(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        rhcpkg = RHCephPkg()
        # Pass a fake cpuinfo file:
        cpuinfo = os.path.join(FIXTURES_DIR, 'cpuinfo')
        result = rhcpkg._get_num_cpus(cpuinfo=cpuinfo)
        assert result == 4


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
