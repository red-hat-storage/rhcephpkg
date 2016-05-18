import os
from rhcephpkg import Build

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class TestBuild(object):

    def setup_method(self, method):
        """ Reset args/kwargs before each test. """
        self.args = []
        self.kwargs = {}

    def fake_build_job(self, *args, **kwargs):
        """ Store args/kwargs, in order to verify later. """
        self.args = args
        self.kwargs = kwargs
        return 0

    def test_working_build(self, monkeypatch):
        monkeypatch.setenv('HOME', FIXTURES_DIR)
        monkeypatch.setattr('jenkins.Jenkins.build_job', self.fake_build_job)
        monkeypatch.setattr('rhcephpkg.util.package_name', lambda: 'mypkg')
        monkeypatch.setattr('rhcephpkg.util.current_branch',
                            lambda: 'ceph-2-ubuntu')
        build = Build(())
        build._run()
        assert self.args == ('build-package',)
        assert self.kwargs == {'parameters': {'BRANCH': 'ceph-2-ubuntu',
                                              'PKG_NAME': 'mypkg'},
                               'token': '5d41402abc4b2a76b9719d911017c592'}
