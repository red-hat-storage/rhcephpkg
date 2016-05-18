import json
import os
import posixpath
import shutil
import six
from six.moves import configparser
from six.moves.urllib.request import Request, urlopen
from tambo import Transport
import rhcephpkg.util as util
import rhcephpkg.log as log


class Download(object):
    help_menu = 'download a build from chacra'
    _help = """
Download a build's entire artifacts from chacra.

Positional Arguments:

[build]  The name of the build to download, eg. "ceph_10.2.0-2redhat1trusty"
"""
    name = 'download'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            build = self.parser.unknown_commands[0]
        except IndexError:
            self.help()
        self._run(build)

    def help(self):
        return self._help

    def _run(self, build):
        configp = util.config()
        try:
            base_url = configp.get('rhcephpkg.chacra', 'url')
        except configparser.Error as err:
            raise SystemExit('Problem parsing .rhcephpkg.conf: %s',
                             err.message)
        (pkg, version) = build.split('_')
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
                    # TODO: check the sha256sum of the already-downloaded file
                    # here?
                    log.info('skipping %s' % binary)
                    continue
                log.info('downloading %s' % binary)
                binary_url = posixpath.join(build_url, arch, binary) + '/'
                response = urlopen(Request(binary_url))
                with open(binary, 'wb') as fp:
                    shutil.copyfileobj(response, fp)
