import json
import os
import re
import httpretty
from rhcephpkg import Download

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


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
        monkeypatch.chdir(tmpdir)
        download = Download(())
        download._run('ceph_10.2.0-2redhat1trusty')
        for binaries in payload.values():
            for binary in binaries:
                assert os.path.isfile(binary)
