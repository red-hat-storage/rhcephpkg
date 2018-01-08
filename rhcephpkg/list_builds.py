import json
import posixpath
import six
from six.moves import configparser
from six.moves.urllib.request import Request, urlopen
from gbp.deb import DpkgCompareVersions
from tambo import Transport
import rhcephpkg.util as util


class ListBuilds(object):
    help_menu = 'list builds for a package in chacra'
    _help = """
Print a sorted list of all builds (NVRs) stored in chacra for a package.

This is somewhat similar to the "koji list-builds" command.

Positional Arguments:

[package]  The name of the package, eg "ceph"
"""
    name = 'list-builds'

    def __init__(self, argv):
        self.argv = argv
        self.options = []

    def main(self):
        self.parser = Transport(self.argv, options=self.options)
        self.parser.catch_help = self.help()
        self.parser.parse_args()
        try:
            package = self.parser.unknown_commands[0]
        except IndexError:
            return self.parser.print_help()
        self._run(package)

    def help(self):
        return self._help

    def _run(self, package):
        versions = self.list_builds(package)
        versions = self.sort_nvrs(versions)
        nvrs = ['%s_%s' % (package, version) for version in versions]
        print("\n".join(nvrs))

    def list_builds(self, package):
        configp = util.config()
        try:
            base_url = configp.get('rhcephpkg.chacra', 'url')
        except configparser.Error as err:
            raise SystemExit('Problem parsing .rhcephpkg.conf: %s',
                             err.message)
        builds_url = posixpath.join(base_url, 'binaries/', package)
        build_response = urlopen(Request(builds_url))
        headers = build_response.headers
        if six.PY2:
            encoding = headers.getparam('charset') or 'utf-8'
            # if encoding is None:
            #    encoding = 'utf-8'
        else:
            encoding = headers.get_content_charset(failobj='utf-8')
        payload = json.loads(build_response.read().decode(encoding))
        return payload.keys()

    def sort_nvrs(self, nvrs):
        dcmp = DpkgCompareVersions()
        if six.PY2:
            return sorted(nvrs, cmp=dcmp)
        from functools import cmp_to_key
        return sorted(nvrs, key=cmp_to_key(dcmp))
