Guide to `rhcephpkg new-version`
================================

You're about to rebase the downstream package to a new upstream version.

There are two ways to do this:

1. Use the "uscan" functionality. This will dynamically find the latest
   upstream tarball from a website, download it, and import it.
   ::

       rhcephpkg new-version

2. Use a pre-existing local tarball that you've already downloaded. Use this if
   uscan is too complicated, or if you want to a high level of confidence that
   your upstream tarball file matches the one RHEL dist-git has.
   ::

       rhcephpkg new-version ../ceph_12.2.4.orig.tar.gz

Note: normally you want to use the ``-B`` flag to indicate which RHBZs you're
resolving with this new upstream version.


Example: rebasing ceph-ansible
------------------------------

This example uses uscan.

Step 1: Assemble the list of RHBZs that this new upstream version of
ceph-ansible will resolve.

Step 2: Clone the package::

    cd ~/ubuntu-scm
    rhcephpkg clone ceph-ansible
    cd ceph-ansible

Step 3: Check out the product-version dist-git branch we want to rebase::

    git checkout ceph-3.0-ubuntu

(This sets up the local branch tracking with origin/ceph-3.0-ubuntu)

One thing to note here:

* ``debian/gbp.conf`` has no ``upstream-vcs-tag`` setting. This means
  ``git-buildpackage`` will not make the upstream version tag a parent of the
  import commit. This means we have no ability to use ``gbp pq export`` to
  manage downstream patches.

  The reason we do not do this for ceph-ansible is that for ceph-ansible betas
  or RCs this will not work. We use uscan to mangle the upstream tag
  "v3.0.0rc12" to the debian-ify'd upstream version "3.0.0~rc12". In other
  words, it may not make sense to use the ``upstream-vcs-tag`` setting for all
  packages or versions.

Step 4: You can now run ``new-version`` with no tarball argument::

    rhcephpkg new-version -B "rhbz#XXXXXX rhbz#XXXXXX"

(rhcephpkg will run ``gbp import-orig`` with ``--uscan``, and add a
``debian/changelog`` entry for this new upstream version along with the
Bugzilla ticket numbers.)


Example: rebasing ceph
----------------------

This example uses a pre-existing local tarball file (not uscan).

Step 1: Assemble the list of RHBZs that this new upstream version of ceph will
resolve.

Step 2: Clone the package::

    cd ~/ubuntu-scm
    rhcephpkg clone ceph
    cd ceph

Step 3: Check out the product-version dist-git branch we want to rebase::

    git checkout ceph-3.0-ubuntu

(This sets up the local branch tracking with origin/ceph-3.0-ubuntu)

One thing to note here:

* ``debian/gbp.conf`` has a ``upstream-vcs-tag = v%(version)s`` setting. This
  means ``git-buildpackage`` will make the upstream version tag a parent of
  the import commit. This allows us to use ``gbp pq export`` to manage
  downstream patches.

Step 4: Place the upstream tarball in the parent directory::

    cd ~/ubuntu-scm

    # (...copy ceph-12.2.4.tar.gz from RHEL dist-git...)

    # Make sure the filename matches Debian's conventions:
    mv ceph-12.2.4.tar.gz ceph_12.2.4.orig.tar.gz

(Note the tarball must be named like this for gbp-import-orig to process the
version number correctly.)

Step 5: You can now run ``new-version`` with the tarball argument::

    rhcephpkg new-version ../ceph_12.2.4.orig.tar.gz -B "rhbz#1548067 rhbz#1544680"

(rhcephpkg will run ``gbp import-orig`` with ``ceph_12.2.4.orig.tar.gz``, and
add a ``debian/changelog`` entry for this new upstream version along with the
Bugzilla ticket numbers.)

Step 6: Ceph itself has a couple of quirks that we need to fix up afterwards.

1. Re-do all the patches::

     git rm -r debian/patches

   If the patch-queue branch still has existing downstream patches after the
   rebase operation, you can re-apply them now with ``rhcephpkg patch``.

2.  Make sure the debian/ directory matches upstream. To go change-by-change::

     git checkout -p v12.2.4 debian/

   Make sure to leave the downstream ``.git_version`` manipulation parts in
   ``debian/rules``, and ``debian/changelog`` should not have the changes from
   upstream.

3.  Make sure the ``debian/rules`` file has the new sha1. You can find the sha1
   for the tag with ``git rev-parse v12.2.4^0``.

We should probably make ``rhcephpkg new-version`` do some or all of these steps
automatically in the future.

Troubleshooting
===============

"upstream" branch does not exist
--------------------------------

Let's say the upstream branch does not exist at all yet. You can just create it from the upstream tag, like so::

    git branch upstream/ceph-3.0-ubuntu v12.2.4

We should probably make ``rhcephpkg new-version`` do that automatically in the
future (maybe with an interactive prompt?)

"pristine-tar" branch does not exist
------------------------------------

If there is no "pristine-tar" branch already, you can create it like so::

   git checkout --orphan pristine-tar

"debian/watch" file not exist
-----------------------------

Let's say you have some debian packaging that lacks a ``debian/watch`` file.

Step 1: Review the documentation at https://wiki.debian.org/debian/watch#GitHub

Step 2: Write your ``debian/watch`` file for your project.

Step 3: Test that it's working::

    uscan --no-download --verbose

Step 4: Commit your ``debian/watch`` file.

Step 5: Run ``new-version`` to import the new version::

    rhcephpkg new-version
