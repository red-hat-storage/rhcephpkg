``rhcephpkg``
=============

.. image:: https://travis-ci.org/red-hat-storage/rhcephpkg.svg?branch=master
          :target: https://travis-ci.org/red-hat-storage/rhcephpkg

.. image:: https://badge.fury.io/py/rhcephpkg.svg
             :target: https://badge.fury.io/py/rhcephpkg

A tool to package and build Red Hat Ceph Storage for Ubuntu.

``rhcephpkg`` is a command-line tool similar to Red Hat's "rpkg" family of
tools, like `fedpkg
<https://fedoraproject.org/wiki/Package_maintenance_guide>`_ (open-source) or
rhpkg (closed-source). In Red Hat we use this to package and build the RH Ceph
Enterprise product for Ubuntu.

Configuration
-------------

``$HOME/.rhcephpkg.conf`` should contain the following::

  [rhcephpkg]
  user=kdreyer
  gitbaseurl = ssh://%(user)s@code.engineering.redhat.com/rcm/ceph-ubuntu/%(module)s
  anongiturl = git://git.app.eng.bos.redhat.com/rcm/ceph-ubuntu/%(module)s.git
  patchesbaseurl = ssh://%(user)s@code.engineering.redhat.com/%(module)s

  [rhcephpkg.jenkins]
  token=5d41402abc4b2a76b9719d911017c592
  url=https://rcm-jenkins.app.eng.bos.redhat.com/

  [rhcephpkg.chacra]
  url=https://ubuntu-ceph-test.brew.prod.eng.bos.redhat.com/

Substitute your settings:

* ``user`` is your Red Hat Kerberos UID
* ``token`` is your API token from Jenkins. To find this value, log into Jenkins' Web UI (using your Kerberos username + password)

Commands
--------

* ``rhcephpkg clone`` - clone a "dist-git" repository. You must have a valid
  Kerberos ticket.

  We use Git repositories with layouts that interoperate with Debian's
  `git-buildpackage
  <http://honk.sigxcpu.org/projects/git-buildpackage/manual-html/gbp.html>`_
  suite of tools.

  The ``clone`` operation uses your SSH key, which must be configured in
  Gerrit.

* ``rhcephpkg build`` - Trigger a build in Jenkins.

* ``rhcephpkg download`` - Download a build's artifacts from chacra.

* ``rhcephpkg hello`` - Test Jenkins authentication. Use this to verify your
  ``user`` and ``token`` settings.

* ``rhcephpkg localbuild`` - Perform a local build using pbuilder.

* ``rhcephpkg merge-patches`` - Do a fast-forward merge from the rdopkg-style
  "patches" remote branch.

* ``rhcephpkg patch`` - Apply a patch-queue branch to a package.

* ``rhcephpkg source`` - Build a source package on the local system.

Installing
----------

Pre-built Ubuntu Trusty packages are available::

  sudo apt-add-repository ppa:kdreyer-redhat/rhceph
  sudo apt-get update
  sudo apt-get install rhcephpkg

TODO
----

* ``rhcephpkg push`` - Runs ``git push origin --tags`` and then
  ``git push origin``. This will help with CI during rebases, so that
  Jenkins (via Gerrit) will pick up the branch change only after the new tags
  are already present.

* ``rhcephpkg dch`` - Bump the changelog according to our "redhat" version
  number change pattern. This will help make rebases faster.

* ``rhcephpkg amend`` - Amend the last Git commit to make the commit
  message align with the last ``debian/changelog`` entry. This would be similar
  to how ``rdopkg amend`` works (and some of this functionality is already
  present in ``rhcephpkg patch``).
