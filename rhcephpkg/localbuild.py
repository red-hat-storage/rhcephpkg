import math
from multiprocessing import cpu_count
import os
import re
import subprocess
from tambo import Transport
import rhcephpkg.log as log
import rhcephpkg.util as util


def setup_pbuilder_cache(pbuilder_cache, distro):
    # Delete existing cache file if it is bogus (zero-length).
    if os.path.isfile(pbuilder_cache):
        if os.stat(pbuilder_cache).st_size == 0:
            log.info('deleting 0 length %s', pbuilder_cache)
            cmd = ['sudo', 'rm', pbuilder_cache]
            subprocess.check_call(cmd)
    # Set up the cache if it does not exist.
    if not os.path.isfile(pbuilder_cache):
        log.info('initializing pbuilder cache %s', pbuilder_cache)
        cmd = ['sudo', 'pbuilder', 'create', '--debootstrapopts',
               '--variant=buildd', '--basetgz', pbuilder_cache,
               '--distribution', distro]
        subprocess.check_call(cmd)


def get_distro():
    """
    Automatically determine the distro to use, based on the dist-git branch
    name.
    """
    branch = util.current_branch()
    branch = re.sub('^private-[^-]+-', '', branch)
    parts = branch.split('-')  # ['ceph', '3.0', 'ubuntu']
    try:
        distro = parts[2]
    except IndexError:
        log.error('could not parse dist-git branch name "%s" distro' % branch)
        log.error('try explicitly specifying a distro with --dist')
        raise
    if distro != 'ubuntu':
        return distro
    if branch.startswith('ceph-1.3'):
        return 'trusty'
    if branch.startswith('ceph-2'):
        return 'xenial'
    if branch.startswith('ceph-3'):
        return 'xenial'
    # TODO: add Ubuntu 18.04 codename here for ceph-4 when available.
    log.error('unknown default distro for dist-git branch name "%s"' % branch)
    raise NotImplementedError('specify --dist')


class Localbuild(object):
    help_menu = 'build a package on the local system'
    _help = """
Build a package on the local system, using pbuilder.

Options:
--dist    "xenial" or "trusty". If unspecified, rhcephpkg will choose one
          based on the current branch's name.

  Rules for automatic distro selection:

    1) If the branch suffix is an ubuntu distro name, use that.
       eg "ceph-3.0-xenial".
    2) If a branch has a version number starting with "1.3", return "trusty".
       eg. "ceph-1.3-ubuntu"
    3) If a branch has a version number starting with "2" return "xenial".
       eg. "ceph-2-ubuntu"
    4) If a branch has a version number starting with "3" return "xenial".
       eg. "ceph-3.0-ubuntu"
    5) Otherwise raise, because we need to add more rules.
"""
    name = 'localbuild'

    def __init__(self, argv):
        self.argv = argv
        self.options = ('--dist',)

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()

        # Allow user to override the distro.
        if self.parser.has('--dist'):
            if self.parser.get('--dist') is None:
                raise SystemExit('Specify a distro to --dist')
            distro = self.parser.get('--dist')
        else:
            distro = get_distro()

        if self.parser.unknown_commands:
            log.error('unknown option %s',
                      ' '.join(self.parser.unknown_commands))
            return self.parser.print_help()

        self._run(distro)

    def help(self):
        return self._help

    def _run(self, distro):
        """ Build a package on the local system, using pbuilder. """
        pkg_name = util.package_name()

        os.environ['BUILDER'] = 'pbuilder'
        j_arg = self._get_j_arg(cpu_count())
        pbuilder_cache = '/var/cache/pbuilder/base-%s-amd64.tgz' % distro

        setup_pbuilder_cache(pbuilder_cache, distro)

        util.setup_pristine_tar_branch()

        # TODO: we should also probably check parent dir for leftovers and warn
        # the user to delete them (or delete them ourselves?)
        cmd = ['gbp', 'buildpackage', '--git-dist=%s' % distro,
               '--git-arch=amd64', '--git-verbose', '--git-pbuilder', j_arg,
               '-us', '-uc']

        log.info('building %s with pbuilder', pkg_name)
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
            # mem_gib is a decimal, eg. 7.707 on 8GB system
            mem_gib = mem_bytes / (1024. ** 3)
            # Round up to the nearest GB for our purposes.
            total_ram_gb = math.ceil(mem_gib)
        number = min(cpus, total_ram_gb / 4)
        return '-j%d' % max(number, 1)
