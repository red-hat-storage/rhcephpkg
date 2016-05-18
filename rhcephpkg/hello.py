import json
import posixpath
from jenkins import JenkinsException
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError
from six.moves.http_client import BadStatusLine
from tambo import Transport

import rhcephpkg.util as util


class Hello(object):
    help_menu = 'test authentication to Jenkins'
    _help = """
Test authentication to Jenkins and return your user's fullName attribute.
"""
    name = 'hello'

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
        """ Authenticate to Jenkins and print our username to STDOUT.
            Useful for checking that our authentication credentials are
            correct. """
        jenkins = util.jenkins_connection()
        # python-jenkins does not have syntactic support for "whoami" (the
        # "/me/api/json" endpoint), so we have to hit it and parse it
        # ourselves.
        # https://review.openstack.org/307896

        whoami_url = posixpath.join(jenkins.url, 'me/api/json')
        try:
            response = jenkins.jenkins_open(Request(whoami_url))
            data = json.loads(response)
        except JenkinsException as err:
            raise SystemExit(err)

        name = data['fullName']  # Our Jenkins instance gets this from LDAP
        try:
            jenkins_version = jenkins.get_version()
        except AttributeError:
            # python-jenkins older than 0.4.1 does not have get_version().
            version_url = jenkins.server
            try:
                response = urlopen(Request(version_url))
                jenkins_version = response.info().getheader('X-Jenkins')
            except (HTTPError, BadStatusLine) as err:
                raise SystemExit(err)
        print('Hello %s from Jenkins %s' % (name, jenkins_version))
