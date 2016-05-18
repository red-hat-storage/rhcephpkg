import math
from multiprocessing import cpu_count
import os
import subprocess
from tambo import Transport
import rhcephpkg.log as log
import rhcephpkg.util as util


class Localbuild(object):
    help_menu = 'build a package on the local system'
    _help = """
Build a package on the local system, using pbuilder.
"""
    name = 'localbuild'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()

        # FIXME: stop hardcoding trusty. Use the git branch name instead,
        # translating "-ubuntu" into this local computer's own distro.
        distro = 'trusty'

        self._run(distro)

    def help(self):
        return self._help

    def _run(self, distro):
        """ Build a package on the local system, using pbuilder. """
        pkg_name = util.package_name()

        os.environ['BUILDER'] = 'pbuilder'
        j_arg = self._get_j_arg(cpu_count())
        pbuilder_cache = '/var/cache/pbuilder/base-%s-amd64.tgz' % distro
        if not os.path.isfile(pbuilder_cache):
            cmd = ['sudo', 'pbuilder', 'create', '--debootstrapopts',
                   '--variant=buildd', '--basetgz', pbuilder_cache,
                   '--distribution', distro]
            log.info('initializing pbuilder cache %s', pbuilder_cache)
            subprocess.check_call(cmd)
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
            mem_gib = mem_bytes/(1024.**3)  # decimal, eg. 7.707 on 8GB system
            # Round up to the nearest GB for our purposes.
            total_ram_gb = math.ceil(mem_gib)
        number = min(cpus, total_ram_gb / 4)
        return '-j%d' % max(number, 1)
