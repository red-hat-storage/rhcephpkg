#!/bin/bash
  
set -euv

pip install pytest-flake8

pip install pytest-cov python-coveralls

# Install the version from GitHub master by default.
# Note: 0.9 is the first gbp version to include full py3 support.
# Things like `gbp pq export` are broken on py3 before this version.
GIT_BUILDPACKAGE_SOURCE=${GIT_BUILDPACKAGE_SOURCE:-master}

declare -A GBP_SOURCES
GBP_SOURCES[xenial]=http://us.archive.ubuntu.com/ubuntu/pool/universe/g/git-buildpackage/git-buildpackage_0.7.2.tar.xz
GBP_SOURCES[bionic]=http://us.archive.ubuntu.com/ubuntu/pool/universe/g/git-buildpackage/git-buildpackage_0.9.8.tar.xz
GBP_SOURCES[master]=https://github.com/agx/git-buildpackage/archive/master/git-buildpackage-master.tar.gz

# Install the desired version.

GBP_URL=${GBP_SOURCES[$GIT_BUILDPACKAGE_SOURCE]}
GBP_FILE=$(basename ${GBP_URL})
GBP_DIR=$(echo $GBP_FILE | sed -e "s/.tar.[gx]z$//" -e "s/_/-/")

if ! type wget > /dev/null; then
  apt-get -y install wget
fi
if ! type xz > /dev/null; then
  apt-get -y install xz-utils
fi


wget -nc $GBP_URL

if [[ "$GBP_FILE" == *.xz ]]; then
  tar xJf ${GBP_FILE}
elif [[ "$GBP_FILE" == *.gz ]]; then
  tar xzf ${GBP_FILE}
fi

pushd $GBP_DIR
  # In old versions, the setuptools packaging really wants to write to
  # /etc/git-buildpackage/gpb.conf, which we cannot access without root.
  sed -i -e '/data_files/d' setup.py
  # setuptools cannot handle utf-8 in "scripts". Affects gbp 0.9.8. Resolved
  # in Git master May 15 2018 (ba32efc1af9e893041dc1752008329b383986786)
  sed -i 's/ü/u/' bin/gbp-builder-mock || :
  python setup.py install
  # gbp depends on dateutil, but setuptools does not pull it in.
  # This packaging bug is fixed in git-buildpackage version 0.8.18.
  pip install python-dateutil
popd
