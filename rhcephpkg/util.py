import os
import subprocess
import pwd
from textwrap import TextWrapper
import time
import six
from six.moves import configparser
from jenkins import Jenkins
try:
    from subprocess import DEVNULL  # py3
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def current_branch():
    """ Ensure we're on a git branch, and returns the current branch's name.

    :raises: subprocess.CalledProcessError if this is not a Git repo, or if
             HEAD is not a valid ref.
    """
    # Note: "git symbolic-ref --short HEAD" will not raise if HEAD is an
    # invalid ref, so we use "git rev-parse" instead to build in that
    # additional check here.
    cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    output = subprocess.check_output(cmd).rstrip()
    if six.PY3:
        return output.decode('utf-8')
    return output


def current_patch_queue_branch():
    """ Get our patch-queue branch's name, based on the current branch """
    current = current_branch()
    if current.startswith('patch-queue/'):
        return current
    else:
        return 'patch-queue/' + current


def current_debian_branch():
    """ Get our debian branch's name, based on the current branch """
    current = current_branch()
    if current.startswith('patch-queue/'):
        return current[12:]
    else:
        return current


def ensure_local_branch(branch, output=False):
    """
    Ensure our local branch exists, tracks origin, and is pointed at the same
    sha1 as the origin remote's branch.
    """
    cmd = ['git', 'branch', '--force', '--track', branch, 'origin/%s' % branch]
    if output:
        subprocess.call(cmd)
    else:
        subprocess.call(cmd, stdout=DEVNULL, stderr=DEVNULL)


def ensure_patch_queue_branch():
    """
    Ensure our local patch-queue branch exists and tracks/matches origin.
    """
    pq_branch = current_patch_queue_branch()
    ensure_local_branch(pq_branch)


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
    cwd = os.getcwd()
    if not os.path.isdir(os.path.join(cwd, '.git')):
        raise RuntimeError('%s is not the root of a git clone' % cwd)
    return os.path.basename(cwd)


def setup_pristine_tar_branch():
    """ Ensure .git/refs/heads/pristine-tar is set up. """
    # Note, gbp has a ``has_pristine_tar_branch`` method. Could we use that?
    if not os.path.exists('.git/refs/remotes/origin/pristine-tar'):
        # If there is no "origin/pristine-tar" branch, this package doesn't use
        # pristine-tar, and we don't care.
        return
    ensure_local_branch('pristine-tar', output=True)


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
    if 'DEBEMAIL' in os.environ:
        return os.environ['DEBEMAIL']
    if 'EMAIL' in os.environ:
        return os.environ['EMAIL']
    c = config()
    return c.get('rhcephpkg', 'user') + '@redhat.com'


def bump_changelog(changes):
    """ Bump the release value in this changelog. Almost identical to dch, with
    the exception that this will do exactly what we want with "redhat" in the
    version. """
    current = get_deb_version()
    version = current.next()
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
        # self.releasenum is like "4" or "0.4" or "0.0.4" or "4.0.bz123"
        self.releasenum = release.split('redhat', 2)[0]
        # self.redhatint is like "1"
        self.redhatint = int(release.split('redhat', 2)[1])

    def next(self):
        """
        Bump this version number and return a new DebVersion.

        eg. "10.2.0-2redhat1" becomes "10.2.0-3redhat1".
        """
        parts = self.releasenum.split('.')
        newparts = []
        # If all parts look like ints, bump the final one.
        # If we have a part that isn't in int, bump the part immediately
        # preceding that one.
        for i, part in enumerate(parts):
            try:
                int(part)
                newparts.append(part)
            except ValueError:
                newparts += parts[i:]
                i -= 1
                break
        if i == -1:
            # The first part was not an int at all... this is weird and
            # unexpected, but possible in theory. Be safe and just append ".1".
            nextreleasenum = self.releasenum + '.1'
        else:
            # Increment our last part that looked like an int:
            newparts[i] = str(int(newparts[i]) + 1)
            nextreleasenum = '.'.join(newparts)
        full = '%s-%sredhat%i' % (self.version,
                                  nextreleasenum,
                                  self.redhatint)
        return DebVersion(full)

    def __str__(self):
        return '%s-%sredhat%i' % (self.version,
                                  self.releasenum,
                                  self.redhatint)
