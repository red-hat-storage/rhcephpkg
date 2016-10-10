import os
from rhcephpkg import Patch

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class FakePatch(object):
    pass


class TestPatch(object):

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
