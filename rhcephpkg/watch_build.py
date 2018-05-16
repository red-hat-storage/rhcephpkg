import sys
from datetime import datetime
from dateutil import tz
from time import sleep
from tambo import Transport
import posixpath
import rhcephpkg.log as log
import rhcephpkg.util as util


class WatchBuild(object):
    help_menu = 'watch a build-package job in Jenkins'
    _help = """
Watch a particular build-package job in Jenkins.

Positional Arguments:

[id]  The build-package job ID to watch

For example: "rhcephpkg watch-build 328"
"""
    name = 'watch-build'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            build_number = int(self.parser.unknown_commands[0])
        except (IndexError, ValueError):
            return self.parser.print_help()
        self.watch(build_number)

    def help(self):
        return self._help

    def watch(self, build_number):
        jenkins = util.jenkins_connection()

        build_info = jenkins.get_build_info('build-package', build_number)

        job_url = posixpath.join(jenkins.url, 'job', 'build-package',
                                 str(build_number))
        log.info('Watching %s' % job_url)

        pkg_name = self.pkg_name(build_info)

        start_seconds = build_info['timestamp'] / 1000.0
        # rcm-jenkins is uses the America/New_York timezone:
        jenkins_tz = tz.gettz('America/New_York')
        start = datetime.fromtimestamp(start_seconds, jenkins_tz)
        # If you want to convert to local time:
        # start = start.astimezone(tz.tzlocal())
        log.info('Started %s' % start.strftime("%F %r %z"))

        was_building = build_info['building']
        while build_info['building']:
            try:
                elapsed = datetime.now(jenkins_tz) - start
                # TODO: Xenial has python-humanize (humanize.naturaldelta()
                # here)
                (minutes, seconds) = divmod(elapsed.total_seconds(), 60)
                # Clear the previous line:
                msg = '\r%s building for %02d:%02d' % \
                    (pkg_name, minutes, seconds)
                sys.stdout.write(msg)
                sys.stdout.flush()
                sleep(10)
                build_info = jenkins.get_build_info('build-package',
                                                    build_number)
            except KeyboardInterrupt:
                print('')
                log.info('continue watching with `rhcephpkg watch-build %s`' %
                         build_number)
                raise SystemExit()
        if was_building:
            # The above "while" loop will not print a final newline.
            print('')

        end_millis = build_info['timestamp'] + build_info['duration']
        end_seconds = end_millis / 1000.0
        end = datetime.fromtimestamp(end_seconds, jenkins_tz)
        log.info('Ended %s' % end.strftime("%F %r %z"))

        # Show the final build result.
        if build_info['result'] == 'SUCCESS':
            log.info('result is SUCCESS')
        else:
            log.error(build_info['result'])
            raise SystemExit(1)

    def pkg_name(self, build_info):
        """ Return a package name based on this build's information.

        :param build_info: ``dict`` from python-jenkins' get_build_info()
        :returns: ``str``, for example "ceph" or "ceph-ansible".
        """
        pkg_name = None
        for action in build_info['actions']:
            if action.get('_class', '') == 'hudson.model.ParametersAction':
                for parameter in action['parameters']:
                    if parameter['name'] == 'PKG_NAME':
                        pkg_name = parameter['value']
        if pkg_name is None:
            # Maybe the Jenkins job was badly mis-configured or something.
            # This will probably never happen, but let's raise defensively.
            raise RuntimeError('could not find pkg name in %s' % build_info)
        return pkg_name
