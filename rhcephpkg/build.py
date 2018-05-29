from time import sleep
from tambo import Transport
import posixpath
import rhcephpkg.log as log
import rhcephpkg.util as util
from rhcephpkg.watch_build import WatchBuild


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
            log.error('%s is a patch-queue branch' % branch_name)
            msg = 'You can switch to the debian branch with "gbp pq switch"'
            raise SystemExit(msg)

        log.info('building %s branch %s at %s', pkg_name, branch_name,
                 posixpath.join(jenkins.url, 'job', 'build-package'))
        job_params = {'PKG_NAME': pkg_name, 'BRANCH': branch_name}

        queue_number = jenkins.build_job('build-package',
                                         parameters=job_params,
                                         token=jenkins.password)

        # Job is now queued, not yet running.
        log.info('Waiting for build queue #%d' % queue_number)
        log.info('This may be safely interrupted...')
        queue_item = jenkins.get_queue_item(queue_number)
        while 'executable' not in queue_item:
            log.info('queue state: %s' % queue_item['why'])
            sleep(2)
            queue_item = jenkins.get_queue_item(queue_number)

        # Job is now running.
        build_number = queue_item['executable']['number']
        # Pass the rest over to the "watch-build" command.
        watcher = WatchBuild(['watch'])
        watcher.watch(build_number)
