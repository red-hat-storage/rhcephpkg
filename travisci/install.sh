#!/bin/bash
  
set -euv

pip install pytest-flake8

pip install pytest-cov python-coveralls

if [ ${TRAVIS_PYTHON_VERSION:0:1} == 2 ]; then
  # Install the version from Trusty.
  wget http://us.archive.ubuntu.com/ubuntu/pool/universe/g/git-buildpackage/git-buildpackage_0.6.9.tar.xz
  tar xJf git-buildpackage_0.6.9.tar.xz
  # It gets better. The tarball really wants to write to
  # /etc/git-buildpackage/gpb.conf, which we cannot access without root.
  pushd git-buildpackage-0.6.9
    sed -i -e '/data_files/d' setup.py
    python setup.py install
    # gbp depends on dateutil, but setuptools does not pull it in.
    # discussion on git-buildpackage@lists.sigxcpu.org Jul 2017
    pip install python-dateutil
  popd
fi
