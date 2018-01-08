from rhcephpkg import ListBuilds
from rhcephpkg.tests.util import fake_urlopen


class TestListBuilds(object):

    # Note these tests use Python's "sorted()", which is not the same as
    # gbp.deb.DpkgCompareVersions, but it's good enough for this trivial test
    # fixture data.

    def test_list_builds(self, monkeypatch):
        monkeypatch.setattr('rhcephpkg.list_builds.urlopen', fake_urlopen)
        lb = ListBuilds(['rhcephpkg', 'ceph-ansible'])
        versions = lb.list_builds('ceph-ansible')
        expected = [
            '3.0.14-2redhat1',
            '3.0.16-2redhat1',
        ]
        assert sorted(versions) == expected

    def test_sort_nvrs(self):
        lb = ListBuilds(['rhcephpkg', 'ceph-ansible'])
        versions = [
            '3.0.16-2redhat1',
            '3.0.14-2redhat1',
        ]
        sorted_versions = lb.sort_nvrs(versions)
        assert sorted_versions == sorted(versions)

    def test_main(self, monkeypatch, capsys):
        monkeypatch.setattr('rhcephpkg.list_builds.urlopen', fake_urlopen)
        lb = ListBuilds(['rhcephpkg', 'ceph-ansible'])
        lb.main()
        expected = """
ceph-ansible_3.0.14-2redhat1
ceph-ansible_3.0.16-2redhat1
""".lstrip()
        out, _ = capsys.readouterr()
        assert out == expected
