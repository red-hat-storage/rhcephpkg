import subprocess
import six
from rhcephpkg import Patch
import pytest


def git(*args):
    """ shortcut for shelling out to git """
    cmd = ['git'] + list(args)
    output = subprocess.check_output(cmd)
    if six.PY3:
        return output.decode('utf-8').rstrip()
    return output.rstrip()


class TestPatch(object):
    @pytest.fixture
    def testpkg(self, testpkg):
        """
        Override the testpkg fixture with some additional content.

        TODO: just move this all to the main testpkg fixture? What's the
        performance impact? (Note the checked-out branch behavior at the end is
        different...)
        """
        # Add a "foobar" commit to the patch-queue branch.
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        testpkg.join('foobar.py').ensure(file=True)
        git('add', 'foobar.py')
        git('commit', 'foobar.py', '-m', 'add foobar script',
            '-m', 'Resolves: rhbz#123')
        # Note we're not on the debian branch any more, so we implicitly test
        # that path.
        return testpkg

    def test_series_file(self, testpkg):
        """ Verify that we update the debian/patches/series file correctly. """
        pytest.importorskip('gbp')
        series_file = testpkg.join('debian').join('patches').join('series')
        assert not series_file.exists()
        p = Patch([])
        p._run()
        assert series_file.read() == "0001-add-foobar-script.patch\n"

    def test_changelog(self, testpkg):
        """ Verify that we update the debian/changelog file correctly. """
        pytest.importorskip('gbp')
        changelog_file = testpkg.join('debian').join('changelog')
        p = Patch([])
        p._run()
        expected = """
testpkg (1.0.0-3redhat1) stable; urgency=medium

  * add foobar script (rhbz#123)

""".lstrip("\n")
        assert changelog_file.read().startswith(expected)

    def test_rules(self, testpkg):
        """ Verify that we update the debian/rules file correctly. """
        pytest.importorskip('gbp')
        rules_file = testpkg.join('debian').join('rules')
        sha = git('rev-parse', 'patch-queue/ceph-2-ubuntu')
        expected = 'COMMIT=%s' % sha
        assert expected not in rules_file.read()
        p = Patch([])
        p._run()
        assert expected in rules_file.read()

    def test_no_changes(self, testpkg, capsys):
        """ Verify that we bail when no patches have changed. """
        pytest.importorskip('gbp')
        p = Patch([])
        p._run()
        with pytest.raises(SystemExit):
            p._run()
        out, _ = capsys.readouterr()
        assert 'No new patches, quitting.' in out

    def test_amended_patch(self, testpkg, capsys):
        pytest.importorskip('gbp')
        p = Patch([])
        p._run()
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        testpkg.join('foobar.py').write('#!/usr/bin/python')
        git('commit', 'foobar.py', '--amend', '--reset-author', '--no-edit')
        p._run()
        changelog_file = testpkg.join('debian').join('changelog')
        expected = """
testpkg (1.0.0-4redhat1) stable; urgency=medium

  * M  debian/patches/0001-add-foobar-script.patch

""".lstrip("\n")
        assert changelog_file.read().startswith(expected)


class FakePatch(object):
    pass


class TestPatchGetRHBZs(object):

    def test_get_rhbzs(self):
        p = Patch([])
        fakepatch = FakePatch()
        fakepatch.subject = 'my git change'
        fakepatch.long_desc = 'my long description about this change'
        bzs = p.get_rhbzs(fakepatch)
        assert len(bzs) == 0
        # TODO: more tests here, for commits that really contain RHBZs.
