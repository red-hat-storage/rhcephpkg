from tambo import Transport
import posixpath
from pkg_resources import get_distribution, parse_version
import types
import rhcephpkg.log as log
import rhcephpkg.util as util


def _build_job_fixed(self, name, parameters, token):
    """ Workaround for https://bugs.launchpad.net/bugs/1177831 """
    import urllib2  # NOQA
    # Note the final empty string argument here:
    return self.jenkins_open(urllib2.Request(
        self.build_job_url(name, parameters, token), ''))


class Build(object):
    help_menu = 'build a package in Jenkins'
    _help = """
Build a package in Jenkins.
"""
    name = 'build'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        self._run()

    def help(self):
        return self._help

    def _run(self):
        """ Build a package in Jenkins. """
        pkg_name = util.package_name()
        branch_name = util.current_branch()
        jenkins = util.jenkins_connection()

        if branch_name.startswith('patch-queue/'):
            log.error('%s a patch-queue branch' % branch_name)
            msg = 'You can switch to the debian branch with "gbp pq switch"'
            raise SystemExit(msg)

        log.info('building %s branch %s at %s', pkg_name, branch_name,
                 posixpath.join(jenkins.url, 'job', 'build-package'))
        job_params = {'PKG_NAME': pkg_name, 'BRANCH': branch_name}

        if self._has_broken_build_job():
            jenkins.build_job = types.MethodType(_build_job_fixed, jenkins)

        jenkins.build_job('build-package', parameters=job_params,
                          token=jenkins.password)

    def _has_broken_build_job(self):
        # Ubuntu Trusty ships python-jenkins 0.2.1-0ubuntu1, and this version
        # has a broken build_job() method. See
        # https://bugs.launchpad.net/bugs/1177831 .
        # This bug was fixed in python-jenkins v0.3.2 upstream.
        v = get_distribution('python_jenkins').version
        return parse_version(v) < parse_version('0.3.2')
