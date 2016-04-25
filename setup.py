import os
import re
import subprocess
import sys
from setuptools.command.test import test as TestCommand
from setuptools import Command

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
LONG_DESCRIPTION = open(readme).read()

module_file = open("rhcephpkg/__init__.py").read()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


class NewVersionCommand(Command):
    """ Bump the version number on a new "version-" branch """

    def run(self):
        # Bump version and report the number
        export `bumpversion patch --list rhcephpkg/__init__.py`
        # Checkout a new branch with this version number
        echo git checkout -b version-$new_version
        # Make a new commit with this number
        echo git commit -m "version $new_version"


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

        # Push package to pypi
        cmd = ['python', 'setup.py', 'sdist', 'upload']
        if self.sign:
            cmd.append('--sign')
        print(' '.join(cmd))
        subprocess.check_call(cmd)


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
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main('rhcephpkg --flake8 ' + self.pytest_args)
        sys.exit(errno)


from setuptools import setup

setup(
    name             = 'rhcephpkg',
    description      = 'Packaging tool for Red Hat Ceph Storage product',
    packages         = ['rhcephpkg'],
    author           = 'Ken Dreyer',
    author_email     = 'kdreyer [at] redhat.com',
    url              = 'https://github.com/red-hat-storage/rhcephpkg',
    version          = metadata['version'],
    license          = 'MIT',
    zip_safe         = False,
    keywords         = 'packaging, build, rpkg',
    long_description = LONG_DESCRIPTION,
    scripts          = ['bin/rhcephpkg'],
    install_requires = [
        'python-jenkins',
        'six',
        'tambo>=0.1.0',
    ],
    tests_require    = [
        'pytest',
        'pytest-flake8',
        'httpretty',
    ],
    cmdclass = {'newversion': NewVersionCommand,
                'test': PyTest,
                'release': ReleaseCommand},
)
