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
        data = jenkins.get_whoami()
        name = data['fullName']  # Our Jenkins instance gets this from LDAP
        jenkins_version = jenkins.get_version()
        print('Hello %s from Jenkins %s' % (name, jenkins_version))
