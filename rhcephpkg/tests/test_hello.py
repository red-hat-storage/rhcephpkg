import os
import httpretty
from rhcephpkg import Hello

try:
    from jenkins import CRUMB_URL
except ImportError:
    # CRUMB_URL was introduced in python-jenkins v0.2.2
    CRUMB_URL = 'crumbIssuer/api/json'

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


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
        hello = Hello(())
        hello._run()
        out, _ = capsys.readouterr()
        assert out == "Hello Ken from Jenkins 1.5\n"
