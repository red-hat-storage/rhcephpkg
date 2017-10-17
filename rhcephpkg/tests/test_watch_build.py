from rhcephpkg import WatchBuild
from datetime import datetime
import pytest


class FakeJenkins(object):
    def __init__(self):
        self.queried = 0
        dt = datetime.now()
        self.timestamp = dt.microsecond
        self.result = 'SUCCESS'

    def get_build_info(self, job, id_):
        """ Fake information about a ceph package build. """
        if self.queried < 3:
            # Pretend we're still building
            self.queried += 1
            return {
                'actions': [{'_class': 'hudson.model.ParametersAction',
                             'parameters': [{'name': 'PKG_NAME',
                                            'value': 'ceph'}],
                             }],
                'building': True,
                'timestamp': self.timestamp,
            }
        # Pretend we're done building
        return {
            'building': False,
            'timestamp': self.timestamp,
            'duration': 123456,
            'result': self.result
        }


@pytest.fixture
def fake_jenkins():
    return FakeJenkins()


class TestWatchBuild(object):

    def test_no_args(self, capsys):
        watch_build = WatchBuild(['rhcephpkg'])
        with pytest.raises(SystemExit):
            watch_build.main()
        out, _ = capsys.readouterr()
        expected = watch_build._help + "\n"
        assert out == expected

    def test_simple(self, monkeypatch, fake_jenkins):
        monkeypatch.setattr('rhcephpkg.watch_build.sleep', lambda s: None)
        monkeypatch.setattr('jenkins.Jenkins.get_build_info',
                            fake_jenkins.get_build_info)
        watch_build = WatchBuild(['watch-build', 123])
        watch_build.main()
        assert fake_jenkins.queried > 0

    def test_failed_build(self, monkeypatch, fake_jenkins):
        monkeypatch.setattr('rhcephpkg.watch_build.sleep', lambda s: None)
        fake_jenkins.result = 'FAILED'
        monkeypatch.setattr('jenkins.Jenkins.get_build_info',
                            fake_jenkins.get_build_info)
        watch_build = WatchBuild(['watch-build', 123])
        with pytest.raises(SystemExit):
            watch_build.main()
