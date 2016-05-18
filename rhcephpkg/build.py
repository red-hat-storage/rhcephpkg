from tambo import Transport
import posixpath
import rhcephpkg.log as log
import rhcephpkg.util as util


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

        log.info('building %s branch %s at %s', pkg_name, branch_name,
                 posixpath.join(jenkins.url, 'job', 'build-package'))
        job_params = {'PKG_NAME': pkg_name, 'BRANCH': branch_name}

        jenkins.build_job('build-package', parameters=job_params,
                          token=jenkins.password)
