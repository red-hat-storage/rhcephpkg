from time import sleep
import os
import re
import subprocess
import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup, Command
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
LONG_DESCRIPTION = open(readme).read()


def read_module_contents():
    with open('rhcephpkg/__init__.py') as app_init:
        return app_init.read()


module_file = read_module_contents()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


class BumpCommand(Command):
    """ Bump the __version__ number and commit all changes. """

    user_options = [('version=', 'v', 'version number to use')]

    def initialize_options(self):
        new_version = metadata['version'].split('.')
        new_version[-1] = str(int(new_version[-1]) + 1)  # Bump the final part
        self.version = ".".join(new_version)

    def finalize_options(self):
        pass

    def run(self):

        print('old version: %s  new version: %s' %
              (metadata['version'], self.version))
        try:
            input('Press enter to confirm, or ctrl-c to exit >')
        except KeyboardInterrupt:
            raise SystemExit("\nNot proceeding")

        old = "__version__ = '%s'" % metadata['version']
        new = "__version__ = '%s'" % self.version
        module_file = read_module_contents()
        with open('rhcephpkg/__init__.py', 'w') as fileh:
            fileh.write(module_file.replace(old, new))

        # Commit everything with a standard commit message
        cmd = ['git', 'commit', '-a', '-m', 'version %s' % self.version]
        print(' '.join(cmd))
        subprocess.check_call(cmd)


class ReleaseCommand(Command):
    """ Tag and push a new release. """

    user_options = [('sign', 's', 'GPG-sign the Git tag and release files')]

    def initialize_options(self):
        self.sign = False

    def finalize_options(self):
        pass

    def run(self):
        # Create Git tag
        tag_name = 'v%s' % version
        cmd = ['git', 'tag', '-a', tag_name, '-m', 'version %s' % version]
        if self.sign:
            cmd.append('-s')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push Git tag to origin remote
        cmd = ['git', 'push', 'origin', tag_name]
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Wait for CI to build this tag, so we can push directly to master
        sha1 = self.sha1()
        print('waiting 5 min for Travis CI to mark %s as green' % sha1)
        sleep(5 * 60)
        state = self.ci_state(sha1)
        while state == 'pending':
            print('Travis CI is %s for %s ...' % (state, sha1))
            sleep(45)
            state = self.ci_state(sha1)
        assert state == 'success'

        # Push master to the remote
        cmd = ['git', 'push', 'origin', 'master']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Create source package
        cmd = ['python', 'setup.py', 'sdist']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        tarball = 'dist/%s-%s.tar.gz' % ('rhcephpkg', version)

        # GPG sign
        if self.sign:
            cmd = ['gpg2', '-b', '-a', tarball]
            print(' '.join(cmd))
            subprocess.check_call(cmd)

        # Upload
        cmd = ['twine', 'upload', tarball]
        if self.sign:
            cmd.append(tarball + '.asc')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

    def sha1(self):
        cmd = ['git', 'rev-parse', 'HEAD']
        print(' '.join(cmd))
        output = subprocess.check_output(cmd).strip()
        if sys.version_info[0] == 2:
            return output
        return output.decode('utf-8')

    def ci_state(self, sha1):
        """ Look up GitHub's status for this sha1 ref """
        import requests
        # See https://developer.github.com/v3/repos/statuses/
        url = 'https://api.github.com/' \
              'repos/red-hat-storage/rhcephpkg/commits/%s/status' % sha1
        preview = 'application/vnd.github.howard-the-duck-preview+json'
        response = requests.get(url, headers={'Accept': preview})
        response.raise_for_status()
        data = response.json()
        return data['state']


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main('rhcephpkg --flake8 ' + self.pytest_args)
        sys.exit(errno)


setup(
    name='rhcephpkg',
    description='Packaging tool for Red Hat Ceph Storage product',
    packages=['rhcephpkg'],
    author='Ken Dreyer',
    author_email='kdreyer@redhat.com',
    url='https://github.com/red-hat-storage/rhcephpkg',
    version=metadata['version'],
    license='MIT',
    zip_safe=False,
    keywords='packaging, build, rpkg',
    long_description=LONG_DESCRIPTION,
    scripts=['bin/rhcephpkg'],
    install_requires=[
        'gbp',
        'python-bugzilla',
        'python-jenkins>=1.0.0',
        'six',
        'tambo>=0.1.0',
    ],
    tests_require=[
        'pytest',
        'pytest-flake8',
    ],
    cmdclass={'test': PyTest, 'bump': BumpCommand, 'release': ReleaseCommand},
)
