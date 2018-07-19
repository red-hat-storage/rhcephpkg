Take a deep breath...

Part 1: Creating a new upstream release
=======================================

Switch to the master branch::

  git checkout master

Bump the version number and commit the change::

  python setup.py bump --version 1._._

*Note:* If the changes are minimal, you can omit ``--version`` and ``setup.py
bump`` will automatically choose to increment the version number. You can check
the new resulting commit with ``git show``, or amend this commit if needed,
etc. ``setup.py bump`` is just a local operation.

Next, push your new version. This creates a new tag, new tarball on PyPI, and
pushes the tag and change to the origin remote::

  python setup.py release

This takes a while for Travis CI to build the "version bump commit", and
GitHub has a strict gate for pushes to the master branch.

At the end of this first step, you should have a shiny new tag on the master
branch and a tarball in PyPI. https://pypi.python.org/pypi/rhcephpkg

Part 2: Releasing to rhceph PPA
===============================

This part requires an Ubuntu system (I'm using Xenial).

Change to the standard ubuntu package dist-git location::

  cd ~/ubuntu-scm

Clone the internal repository with the debian packaging, "dist-git" repo::

  git clone ssh://kdreyer@git.engineering.redhat.com/srv/git/users/kdreyer/ubuntu/rhcephpkg

(In hindsight, it was a mistake to store the debian packaging bits separately)

Change to the "xenial" branch::

  cd rhcephpkg
  git checkout xenial

Add the upstream remote::

  git remote add -f upstream https://github.com/red-hat-storage/rhcephpkg

Merge your new tag to the "xenial" branch::

  git merge v1._._

Add a new ``debian/changelog`` entry::

  dch "Update to latest upstream release"

(copy and paste from the older one is fine)

Commit your change to ``debian/changelog``::

  git commit debian/changelog -m 'debian: 1._._-1'

Build the source package (yep we use rhcephpkg to release rhcephpkg)::

  rhcephpkg source

This will run for a bit. At the end you will have a
``rhcephpkg_1._._-1_source.changes`` file and some other source files in your
parent directory (``~/ubuntu-scm``).

Now you must GPG-sign the source files. The ``debsign`` utility will do this.
Setting up GPG is beyond the scope of this document. I've written a `blog post
<http://blog.ktdreyer.com/2017/06/forwarding-gpg-agent-to-container.html>`_
regarding how I manage my personal GPG key on my Yubikey. The important part is
that you sign with ``debsign``::

  debsign -p gpg2 rhcephpkg_1._._-1_source.changes

Now we're almost ready to upload the package to the PPA.

If you happen to be using ``gpg2`` for signing as well, before you run ``dput``
in the next step, you must ensure your GPG public key is present in the old
GPGv1 key store. ``dput`` will only use GPGv1 to verify the signatures
(arguably a bug in ``dput``.) So in my case I must import my public key into
the gpg1 keystore::

  gpg --keyserver keys.fedoraproject.org --recv 478A947F782096AC

Now we're ready to upload to the PPA::

  dput ppa:kdreyer-redhat/rhceph rhcephpkg_1._._-1_source.changes

Launchpad will send an email shortly indiciating that the package has been
accepted. Watch this page to check the status:
https://launchpad.net/~kdreyer-redhat/+archive/ubuntu/rhceph/+packages

Once the Launchpad web UI indicates that the build is complete *and* published,
push your changes to the internal dist-git repository::

  git push origin xenial

Lastly, we also need to copy the package to the older Ubuntu distros we
support. As of this writing, we build the package in the PPA for Xenial only,
so there's nothing to copy now.

At this point you should have your new rhcephpkg version available as a .deb
for Xenial. You can install the new version on your system::

  sudo apt-get update
  sudo apt-get -y install rhcephpkg
  rhcephpkg --version
