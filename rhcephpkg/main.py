import math
import logging
import os
import posixpath
import json
import shutil
import six
import subprocess
import sys
from multiprocessing import cpu_count
from six.moves import configparser
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError
from six.moves.http_client import BadStatusLine

from jenkins import Jenkins, JenkinsException

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
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
        self.jenkins.url = self.config['jenkins_url']

        # Poor mans arg parsing
        if len(sys.argv) < 2:
            print('%s:' % os.path.basename(sys.argv[0]))
            print('valid args are: build, clone, hello, localbuild')
        elif sys.argv[1] == 'build':
            self.build()
        elif sys.argv[1] == 'clone':
            self.clone()
        elif sys.argv[1] == 'download':
            self.download()
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
            config['chacra_url'] = configp.get('rhcephpkg.chacra', 'url')
        except configparser.Error as err:
            log.error('Problem parsing .rhcephpkg.conf: %s', err.message)
            exit(1)
        return config

    def hello_jenkins(self):
        """ Authenticate to Jenkins and print our username to STDOUT.
            Useful for checking that our authentication credentials are
            correct. """
        # python-jenkins does not have syntactic support for "whoami" (the
        # "/me/api/json" endpoint), so we have to hit it and parse it
        # ourselves.
        # https://review.openstack.org/307896

        whoami_url = posixpath.join(self.config['jenkins_url'], 'me/api/json')
        try:
            response = self.jenkins.jenkins_open(Request(whoami_url))
            data = json.loads(response)
        except JenkinsException as err:
            print(err)
            exit(1)

        name = data['fullName']  # Our Jenkins instance gets this from LDAP
        try:
            jenkins_version = self.jenkins.get_version()
        except AttributeError:
            # python-jenkins older than 0.4.1 does not have get_version().
            version_url = self.jenkins.server
            try:
                response = urlopen(Request(version_url))
                jenkins_version = response.info().getheader('X-Jenkins')
            except (HTTPError, BadStatusLine) as err:
                raise SystemExit(err)
        print('Hello %s from Jenkins %s' % (name, jenkins_version))

    def build(self):
        """ Build a package in Jenkins. """
        pkg_name = os.path.basename(os.getcwd())
        # Get our current branch's name
        cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        branch_name = subprocess.check_output(cmd).rstrip()

        log.info('building %s branch %s at %s', pkg_name, branch_name,
                 posixpath.join(self.jenkins.url, 'job', 'build-package'))
        job_params = {'PKG_NAME': pkg_name, 'BRANCH': branch_name}

        self.jenkins.build_job('build-package', parameters=job_params,
                               token=self.jenkins.password)

    def clone(self):
        """ Clone a package from dist-git. """
        pkg = sys.argv[2]
        if os.path.exists(pkg):
            log.error('%s already exists in current working directory.', pkg)
            exit(1)
        pkg_url = self.config['gitbaseurl'] % {'user': self.config['user'],
                                               'module': pkg}
        cmd = ['git', 'clone', pkg_url]
        subprocess.check_call(cmd)

    def download(self):
        """
        Download a build's entire artifacts from chacra.

        Pass an argv like "ceph_10.2.0-2redhat1trusty"
        """
        try:
            build = sys.argv[2]
        except IndexError:
            msg = 'download: specify a build to download, such as ' \
                  'ceph_10.2.0-2redhat1trusty'
            raise SystemExit(msg)
        (pkg, version) = build.split('_')
        base_url = self.config['chacra_url']
        build_url = posixpath.join(base_url, 'binaries/', pkg, version,
                                   'ubuntu', 'all')
        log.info('searching %s for builds' % build_url)
        build_response = urlopen(Request(build_url))
        headers = build_response.headers
        if six.PY2:
            encoding = headers.getparam('charset') or 'utf-8'
            # if encoding is None:
            #    encoding = 'utf-8'
        else:
            encoding = headers.get_content_charset(failobj='utf-8')
        payload = json.loads(build_response.read().decode(encoding))
        for arch, binaries in six.iteritems(payload):
            for binary in binaries:
                if os.path.isfile(binary):
                    log.info('skipping %s' % binary)
                    continue
                log.info('downloading %s' % binary)
                binary_url = posixpath.join(build_url, arch, binary) + '/'
                response = urlopen(Request(binary_url))
                with open(binary, 'wb') as fp:
                    shutil.copyfileobj(response, fp)

    def localbuild(self):
        """ Build a package on the local system, using pbuilder. """
        pkg_name = os.path.basename(os.getcwd())
        os.environ['BUILDER'] = 'pbuilder'
        j_arg = self._get_j_arg(cpu_count())
        # FIXME: stop hardcoding trusty. Use the git branch name instead,
        # translating "-ubuntu" into this local computer's own distro.
        distro = 'trusty'
        pbuilder_cache = '/var/cache/pbuilder/base-%s-amd64.tgz' % distro
        if not os.path.isfile(pbuilder_cache):
            cmd = ['sudo', 'pbuilder', 'create', '--debootstrapopts',
                   '--variant=buildd', '--basetgz', pbuilder_cache,
                   '--distribution', distro]
            log.info('initializing pbuilder cache %s', pbuilder_cache)
            subprocess.check_call(cmd)
        cmd = ['gbp', 'buildpackage', '--git-dist=%s' % distro,
               '--git-arch=amd64', '--git-verbose', '--git-pbuilder', j_arg,
               '-us', '-uc']
        # TODO: we should also probably check parent dir for leftovers and warn
        # the user to delete them (or delete them ourselves?)

        log.info('building %s with pbuilder', pkg_name)
        subprocess.check_call(cmd)

    def source(self):
        """ Build a source package on the local system. """
        cmd = ['gbp', 'buildpackage', '--git-tag', '--git-retag', '-S',
               '-us', '-uc']
        log.info(' '.join(cmd))
        subprocess.check_call(cmd)

    def _get_j_arg(self, cpus, total_ram_gb=None):
        """
        Returns a string like "-j4" or "-j8". j is the number of processors,
        with a maximum of x, where x = TOTAL_RAM_GB / 4.

        We want to use all our processors (a high "j" value), but the build
        process will fail with an "out of memory" error out if this j value is
        too high.

        An 8 GB system would have a maximum of -j2
        A 16 GB system would have a maximum of -j4
        A 32 GB system would have a maximum of -j8
        """
        if total_ram_gb is None:
            page_size = os.sysconf('SC_PAGE_SIZE')
            mem_bytes = page_size * os.sysconf('SC_PHYS_PAGES')
            mem_gib = mem_bytes/(1024.**3)  # decimal, eg. 7.707 on 8GB system
            # Round up to the nearest GB for our purposes.
            total_ram_gb = math.ceil(mem_gib)
        number = min(cpus, total_ram_gb / 4)
        return '-j%d' % max(number, 1)
