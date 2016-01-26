import os
import re

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
LONG_DESCRIPTION = open(readme).read()

module_file = open("rhcephpkg/__init__.py").read()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))


from setuptools import setup

setup(
    name             = 'rhcephpkg',
    description      = 'Packaging tool for Red Hat Ceph Storage product',
    packages         = ['rhcephpkg'],
    author           = 'Ken Dreyer',
    author_email     = 'kdreyer [at] redhat.com',
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
        'httpretty',
    ]
)
