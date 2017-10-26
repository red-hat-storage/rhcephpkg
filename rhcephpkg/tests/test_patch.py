from rhcephpkg import Patch
import pytest
from rhcephpkg.tests.util import git


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
        series_file = testpkg.join('debian').join('patches').join('series')
        assert not series_file.exists()
        p = Patch([])
        p.main()
        assert series_file.read() == "0001-add-foobar-script.patch\n"

    def test_changelog(self, testpkg):
        """ Verify that we update the debian/changelog file correctly. """
        changelog_file = testpkg.join('debian').join('changelog')
        p = Patch([])
        p.main()
        expected = """
testpkg (1.0.0-3redhat1) stable; urgency=medium

  * add foobar script (rhbz#123)

""".lstrip("\n")
        result = changelog_file.read()
        assert result.startswith(expected)

    def test_rules(self, testpkg):
        """ Verify that we update the debian/rules file correctly. """
        rules_file = testpkg.join('debian').join('rules')
        sha = git('rev-parse', 'patch-queue/ceph-2-ubuntu')
        expected = 'COMMIT=%s' % sha
        assert expected not in rules_file.read()
        p = Patch([])
        p.main()
        assert expected in rules_file.read()

    def test_no_changes(self, testpkg, capsys):
        """ Verify that we bail when no patches have changed. """
        p = Patch([])
        p.main()
        with pytest.raises(SystemExit):
            p.main()
        out, _ = capsys.readouterr()
        assert 'No new patches, quitting.' in out

    def test_amended_patch(self, testpkg, capsys):
        p = Patch([])
        p.main()
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        testpkg.join('foobar.py').write('#!/usr/bin/python')
        git('commit', 'foobar.py', '--amend', '--reset-author', '--no-edit')
        p.main()
        changelog_file = testpkg.join('debian').join('changelog')
        expected = """
testpkg (1.0.0-4redhat1) stable; urgency=medium

  * Modified debian/patches/0001-add-foobar-script.patch (rhbz#123)

""".lstrip("\n")
        result = changelog_file.read()
        assert result.startswith(expected)

    def test_delete_earlier_patch(self, testpkg, capsys):
        """
        Verify behavior when we delete an earlier .patch file and the others
        are renamed.
        """
        p = Patch([])
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        # Add a second "baz" commit:
        testpkg.join('baz.py').write('#!/usr/bin/python')
        git('add', 'baz.py')
        git('commit', 'baz.py', '-m', 'add baz script',
            '-m', 'Resolves: rhbz#456')
        testpkg.join('baz.py').ensure(file=True)
        # Commit both "foobar" and "baz" patches to the dist-git branch:
        p.main()
        # Delete both the "foobar" and "baz" patches from our patch-queue:
        git('checkout', 'patch-queue/ceph-2-ubuntu')
        git('reset', '--hard', 'HEAD~2')
        # But really keep the "baz" patch:
        git('cherry-pick', 'HEAD@{4}')  # this is too fragile :(
        p.main()
        changelog_file = testpkg.join('debian').join('changelog')
        # Verify we do not mention "baz" here, since it was simply
        # rebased/renumbered:
        expected = """
testpkg (1.0.0-4redhat1) stable; urgency=medium

  * Deleted debian/patches/0001-add-foobar-script.patch (rhbz#123)

""".lstrip("\n")
        result = changelog_file.read()
        assert result.startswith(expected)


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
