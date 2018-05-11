from rhcephpkg import Build
import pytest


class FakeDistribution(object):
    def __init__(self, version):
        self.version = version


class TestBuild(object):

    def setup_method(self, method):
        """ Reset args/kwargs before each test. """
        self.args = []
        self.kwargs = {}

    def fake_build_job(self, *args, **kwargs):
        """ Store args/kwargs, in order to verify later. """
        self.args = args
        self.kwargs = kwargs
        return 123  # return a fake queue ID number.

    def fake_get_queue_item(self, id_):
        """ Return fake information about a build ID """
        return {'executable': {'number': 456}}  # return a fake build number.

    def fake_get_build_info(self, build_name, id_):
        """ Return fake information about a queue ID """
        return {'building': False, 'duration': 123456, 'result': 'SUCCESS'}

    def test_wrong_branch(self, monkeypatch):
        monkeypatch.setattr('rhcephpkg.util.package_name', lambda: 'mypkg')
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'patch-queue/ceph-2-ubuntu')
        build = Build(['build'])
        with pytest.raises(SystemExit) as e:
            build.main()
        expected = 'You can switch to the debian branch with "gbp pq switch"'
        assert str(e.value) == expected

    def test_working_build(self, monkeypatch):
        monkeypatch.setattr('jenkins.Jenkins.build_job', self.fake_build_job)
        monkeypatch.setattr('jenkins.Jenkins.get_queue_item',
                            self.fake_get_queue_item)
        monkeypatch.setattr('rhcephpkg.watch_build.WatchBuild.watch',
                            lambda self, build_id: None)
        monkeypatch.setattr('rhcephpkg.util.package_name', lambda: 'mypkg')
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'ceph-2-ubuntu')
        build = Build(['build'])
        build.main()
        assert self.args == ('build-package',)
        assert self.kwargs == {'parameters': {'BRANCH': 'ceph-2-ubuntu',
                                              'PKG_NAME': 'mypkg'},
                               'token': '5d41402abc4b2a76b9719d911017c592'}
