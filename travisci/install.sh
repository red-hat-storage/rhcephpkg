#!/bin/bash
  
set -euv

pip install pytest-flake8

pip install pytest-cov python-coveralls

if [ ${TRAVIS_PYTHON_VERSION:0:1} == 2 ]; then
  pip install -e git+https://github.com/agx/git-buildpackage@debian/0.6.9#egg=git-buildpackage-0.6.9
fi
