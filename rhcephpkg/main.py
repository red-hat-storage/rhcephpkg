import logging
import os
import posixpath
import json
import re
import subprocess
import sys
from six.moves import configparser
from six.moves.urllib.request import Request

from jenkins import Jenkins, JenkinsException

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('rhcephpkg')

class RHCephPkg(object):
    """ Main class for rhcephpkg CLI. """

    def __init__(self):
        self.config = self._load_config_from_file()

        self.jenkins = Jenkins(
            self.config['jenkins_url'],
            username=self.config['user'],
            password=self.config['jenkins_token'],
        )
        self.jenkins.password = self.config['jenkins_token']

        # Poor mans arg parsing
        if len(sys.argv) < 2:
            print('%s:' % os.path.basename(sys.argv[0]))
            print('valid args are: build, clone, hello, localbuild')
        elif sys.argv[1] == 'build':
            self.build()
        elif sys.argv[1] == 'clone':
            self.clone()
        elif sys.argv[1] == 'hello':
            self.hello_jenkins()
        elif sys.argv[1] == 'localbuild':
            self.localbuild()

    def _load_config_from_file(self):
        """ Parse a Jenkins configuration file and return a
            username/password/url dict. """

        configp = configparser.RawConfigParser()
        configp.read(os.path.expanduser('~/.rhcephpkg.conf'))

        config = {}
        try:
            config['user'] = configp.get('rhcephpkg', 'user')
            config['gitbaseurl'] = configp.get('rhcephpkg', 'gitbaseurl')
            config['jenkins_token'] = configp.get('rhcephpkg.jenkins', 'token')
            config['jenkins_url'] = configp.get('rhcephpkg.jenkins', 'url')
        except configparser.Error as err:
            log.error('Problem parsing .rhcephpkg.conf: %s', err.message)
            exit(1)
        return config

    def _get_num_cpus(self, cpuinfo='/proc/cpuinfo'):
        """ Get the number of CPUs from /proc/cpuinfo.
            (We will pass this number to pbuilder.) """
        pattern = re.compile('^processor')
        with open(cpuinfo) as f:
            result = filter(lambda x: pattern.match(x), f.readlines())
        return len(list(result))

    def hello_jenkins(self):
        """ Authenticate to Jenkins and print our username to STDOUT.
            Useful for checking that our authentication credentials are
            correct. """
        # python-jenkins does not have syntactic support for "whoami" (the
        # "/me/api/json" endpoint), so we have to hit it and parse it
        # ourselves.

        whoami_url = posixpath.join(self.config['jenkins_url'], 'me/api/json')
        try:
            response = self.jenkins.jenkins_open(Request(whoami_url))
            data = json.loads(response)
        except JenkinsException as err:
            print(err)
            exit(1)

        name = data['fullName'] # Our Jenkins instance gets this from LDAP
        print('Hello %s from Jenkins %s' % (name, self.jenkins.get_version()))

    def build(self):
        """ Build a package in Jenkins. """
        pkg_name = os.path.basename(os.getcwd())
        # Get our current branch's name
        cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        branch_name = subprocess.check_output(cmd).rstrip()

        log.info('building %s branch %s', pkg_name, branch_name)
        job_params = {'PKG_NAME': pkg_name, 'BRANCH': branch_name}

        self.jenkins.build_job(
            'build-package', parameters=job_params, token=self.jenkins.password)

    def clone(self):
        """ Clone a package from dist-git. """
        pkg = sys.argv[2]
        if os.path.exists(pkg):
            log.error('%s already exists in current working directory.', pkg)
            exit(1)
        pkg_url = self.config['gitbaseurl'] % {'user': self.config['user'], 'module': pkg}
        cmd = ['git', 'clone', pkg_url]
        subprocess.check_call(cmd)

    def localbuild(self):
        """ Build a package on the local system, using pbuilder. """
        pkg_name = os.path.basename(os.getcwd())
        # Get our current branch's name
        os.environ['BUILDER'] = 'pbuilder'
        j_arg = '-j%d' % self._get_num_cpus()
        # FIXME: stop hardcoding trusty. Use the git branch name instead,
        # translating "-ubuntu" into this local computer's own distro.
        cmd = ['git-buildpackage', '--git-dist=trusty', '--git-arch=amd64',
               '--git-verbose', '--git-pbuilder', j_arg, '-us', '-uc']
        # TODO: we should also probably check parent dir for leftovers and warn
        # the user to delete them (or delete them ourselves?)

        log.info('building %s with pbuilder', pkg_name)
        subprocess.check_call(cmd)
