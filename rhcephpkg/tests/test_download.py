import os
from rhcephpkg import Download
from rhcephpkg.tests.util import fake_urlopen


class TestDownload(object):

    def test_basic_download(self, monkeypatch, tmpdir):
        monkeypatch.setattr('rhcephpkg.download.urlopen', fake_urlopen)
        monkeypatch.chdir(tmpdir)
        download = Download(['rhcephpkg', 'ceph_10.2.0-2redhat1trusty'])
        download.main()
        expected = [
            'ceph_10.2.0-2redhat1trusty.debian.tar.gz',
            'ceph_10.2.0-2redhat1trusty.dsc',
            'ceph_10.2.0-2redhat1trusty_amd64.changes',
            'ceph_10.2.0.orig.tar.gz',
            'libcephfs1-dbg_10.2.0-2redhat1trusty_amd64.deb',
            'librbd-dbg_10.2.0-2redhat1trusty_amd64.deb',
            'ceph_10.2.0-2redhat1trusty_amd64.deb',
            'radosgw_10.2.0-2redhat1trusty_amd64.deb',
            'libcephfs-java_10.2.0-2redhat1trusty_all.deb',
        ]
        for binary in expected:
            assert os.path.isfile(binary)
