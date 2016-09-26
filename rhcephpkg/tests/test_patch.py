import os
import pytest
from rhcephpkg import Patch

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class FakePatch(object):
    pass


class TestPatch(object):

    def test_wrong_branch(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'ceph-2-ubuntu')
        patch = Patch(())
        with pytest.raises(SystemExit) as e:
            patch._run()
        assert str(e.value) == 'ceph-2-ubuntu is not a patch-queue branch'

    def test_get_rhbzs(self, monkeypatch):
        p = Patch(())
        fakepatch = FakePatch()
        fakepatch.subject = 'my git change'
        fakepatch.long_desc = 'my long description about this change'
        bzs = p.get_rhbzs(fakepatch)
        assert len(bzs) == 0
        # TODO: more tests here, for commits that really contain RHBZs.

    # TODO: more tests, faking check_call and check_output, to verify that
    # we're running the proper gbp and git commands.
