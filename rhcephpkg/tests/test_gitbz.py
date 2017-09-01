import pytest
from collections import namedtuple
from rhcephpkg import Gitbz
from rhcephpkg.tests.util import git


class FakeAnonymousBugzilla(object):
    def __init__(self, *a, **kw):
        self.logged_in = False


class FakeBugzilla(object):
    def __init__(self, *a, **kw):
        self.logged_in = True

    def getbugs(self, *a, **kw):
        Bug = namedtuple('Bug', ['id', 'flags'])
        flags = [{'name': 'ceph-2.y', 'status': '+'}]
        b = Bug(123, flags)
        return [b]


class TestGitbz(object):

    def test_no_bzs(self, testpkg):
        gitbz = Gitbz([])
        with pytest.raises(SystemExit) as e:
            gitbz.main()
        assert str(e.value) == 'no BZs found'

    def test_not_logged_in(self, testpkg, monkeypatch):
        monkeypatch.setattr('rhcephpkg.gitbz.Bugzilla', FakeAnonymousBugzilla)
        git('commit', '--amend', '-m', 'Resolves: rhbz#123')
        gitbz = Gitbz([])
        with pytest.raises(SystemExit) as e:
            gitbz.main()
        assert str(e.value) == 'Not logged into BZ'

    def test_bad_branch(self, testpkg, monkeypatch):
        git('branch', '-m', 'private-kdreyer-ceph-2-ubuntu')
        gitbz = Gitbz([])
        with pytest.raises(SystemExit) as e:
            gitbz.main()
        assert str(e.value) == ('could not parse debian branch '
                                '"private-kdreyer-ceph-2-ubuntu".')

    @pytest.mark.parametrize("branch,expected", [
        ('ceph-3.0-ubuntu', "Missing ceph-3.0 release flag:\nrhbz#123\n"),
        ('ceph-3.1-ubuntu', "Missing ceph-3.y release flag:\nrhbz#123\n"),
    ])
    def test_bz_missing(self, testpkg, monkeypatch, capsys, branch, expected):
        monkeypatch.setattr('rhcephpkg.gitbz.Bugzilla', FakeBugzilla)
        git('commit', '--amend', '-m', 'Resolves: rhbz#123')
        git('branch', '-m', branch)
        gitbz = Gitbz([])
        with pytest.raises(SystemExit):
            gitbz.main()
        out, _ = capsys.readouterr()
        assert out == expected

    def test_bz_present(self, testpkg, monkeypatch, capsys):
        monkeypatch.setattr('rhcephpkg.gitbz.Bugzilla', FakeBugzilla)
        git('commit', '--amend', '-m', 'Resolves: rhbz#123')
        gitbz = Gitbz([])
        gitbz.main()
        out, _ = capsys.readouterr()
        assert out == "rhbz#123: ceph-2.y+\n"
