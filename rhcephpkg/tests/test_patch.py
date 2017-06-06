from rhcephpkg import Patch


class FakePatch(object):
    pass


class TestPatch(object):

    def test_get_rhbzs(self):
        p = Patch([])
        fakepatch = FakePatch()
        fakepatch.subject = 'my git change'
        fakepatch.long_desc = 'my long description about this change'
        bzs = p.get_rhbzs(fakepatch)
        assert len(bzs) == 0
        # TODO: more tests here, for commits that really contain RHBZs.

    # TODO: more tests, faking check_call and check_output, to verify that
    # we're running the proper gbp and git commands.
