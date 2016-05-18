import os
import subprocess
from six.moves import configparser
from jenkins import Jenkins


def current_branch():
    """ Get our current branch's name """
    cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    return subprocess.check_output(cmd).rstrip()


def config():
    """ Parse an rhcephpkg configuration file and return a ConfigParser object.
    """
    configp = configparser.RawConfigParser()
    configp.read(os.path.expanduser('~/.rhcephpkg.conf'))
    return configp


def jenkins_connection():
        """ Return an initialized python-jenkins object. """
        configp = config()
        try:
            user = configp.get('rhcephpkg', 'user')
            token = configp.get('rhcephpkg.jenkins', 'token')
            url = configp.get('rhcephpkg.jenkins', 'url')
        except configparser.Error as err:
            raise SystemExit('Problem parsing .rhcephpkg.conf: %s',
                             err.message)
        jenkins = Jenkins(url, username=user, password=token)
        # These "password" and "url" attributes are not formally part of
        # python-jenkins' API, but they are nice to make available to consumers
        # (for logging/debugging, for example.)
        jenkins.password = token
        jenkins.url = url
        return jenkins


def package_name():
    """ Get the name of this dist-git package
        (just our current working directory) """
    return os.path.basename(os.getcwd())
