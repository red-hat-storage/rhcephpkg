#!/bin/bash

set -ex

which bumpversion > /dev/null

export `bumpversion patch --list rhcephpkg/__init__.py`

git checkout -b version-$new_version

git commit -m "version $new_version" rhcephpkg/__init__.py

git push -u ktdreyer version-$new_version

hub pull-request -m "version $new_version"

sleep 100s

git checkout master

git merge version-$new_version

git push origin master

git push ktdreyer :version-$new_version

git branch -d version-$new_version

python setup.py release
