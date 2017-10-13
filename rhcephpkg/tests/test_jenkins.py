from rhcephpkg.jenkins import RhcephpkgJenkins
from jenkins import Jenkins


class TestJenkins(object):
    def test_inheritance(self):
        issubclass(RhcephpkgJenkins, Jenkins)

    def test_constructor(self):
        j = RhcephpkgJenkins('https://example.com/')
        assert isinstance(j, Jenkins)
