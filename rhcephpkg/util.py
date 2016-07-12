import os
import subprocess
import pwd
from textwrap import TextWrapper
import time
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


def get_user_fullname():
    """ Get a user's full name, if available. """
    # TODO: use $(git config --get user.name) instead
    if 'DEBFULLNAME' in os.environ:
        return os.environ['DEBFULLNAME']
    if 'NAME' in os.environ:
        return os.environ['NAME']
    return pwd.getpwuid(os.getuid()).pw_gecos


def get_user_email():
    """ Get a user's redhat email. """
    c = config()
    return c.get('rhcephpkg', 'user') + '@redhat.com'


def bump_changelog(changes):
    """ Bump the release value in this changelog. Almost identical to dch, with
    the exception that this will do exactly what we want with "redhat" in the
    version. """
    version = get_deb_version()
    version.releaseint += 1
    with open('debian/changelog') as fileh:
        orig = fileh.read()
    header = "%s (%s) stable; urgency=medium\n" % (package_name(), version)
    footer = " -- %s <%s>  %s\n" % (get_user_fullname(),
                                    get_user_email(),
                                    time.strftime('%a, %d %b %Y %T %z'))
    with open('debian/changelog', 'w') as fileh:
        fileh.write(header)
        fileh.write("\n")
        fileh.write(format_changelog(changes))
        fileh.write("\n")
        fileh.write(footer)
        fileh.write("\n")
        fileh.write(orig)
    return True


def format_changelog(changes):
    """ Return a formatted multi-line string describing each change. """
    wrapper = TextWrapper(initial_indent='  * ', subsequent_indent='    ')
    clog = ""
    for change in changes:
        clog += wrapper.fill(change)
        clog += "\n"
    return clog


def get_deb_version():
    """ Get the current version from a /debian/changelog. """
    with open('debian/changelog') as fh:
        first_header = fh.readline()
    # first_header is like "ceph (10.2.0-4redhat1) stable; urgency=medium"
    vstr = first_header.split(' ', 2)[1][1:-1]
    return DebVersion(vstr)


class DebVersion(object):
    """ Representation of a Debian package version, suitable for manipulation
"""

    def __init__(self, full):
        # full package version is like "10.2.0-4redhat1"
        # self.version is like "10.2.0"
        (self.version, release) = full.split('-', 1)
        # self.releaseint is like "4"
        self.releaseint = int(release.split('redhat', 1)[0])
        # self.redhatint is like "1"
        self.redhatint = int(release.split('redhat', 2)[1])

    def __str__(self):
        return '%s-%iredhat%i' % (self.version,
                                  self.releaseint,
                                  self.redhatint)
