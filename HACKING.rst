It is easy to get up and running with rhcephpkg when installing the rhcephpkg
deb from `the PPA
<https://launchpad.net/~kdreyer-redhat/+archive/ubuntu/rhceph>`_. However, if
you want to test a work-in-progress feature of rhcephpkg directly from Git,
read on.


Using rhcephpkg in a virtualenv
===============================

This walkthrough installs rhcephpkg from Git into a Python virtualenv on
Ubuntu Xenial.

Step 1: getting the system dependencies
---------------------------------------

rhcephpkg (and git-buildpackage) shells out to some system utilities. Instead
of installing the dependencies by hand, it's easier to just install the system
version of rhcephpkg first. Following the steps in README.rst::

    sudo apt-get update
    sudo apt-get -y install software-properties-common
    sudo apt-add-repository ppa:kdreyer-redhat/rhceph
    sudo apt-get update
    sudo apt-get -y install rhcephpkg

To be 100% sure you're using the rhcephpkg in your virtualenv, you can
now remove the old package::

    sudo apt-get -y purge rhcephpkg

At this point all the dependencies are on your system, but rhcephpkg itself
(``/usr/bin/rhcephpkg``) is no longer present.

Step 2: cloning from Git
------------------------

Let's clone from Git to our home directory::

    cd ~/dev
    git clone https://github.com/red-hat-storage/rhcephpkg
    cd rhcephpkg

If you need to switch to some branch other than "master", you can do so here.

Step 3: entering a new virtualenv
---------------------------------

Now create a new virtualenv directory and activate it in your current shell::

    sudo apt-get -y install virtualenv
    virtualenv venv
    . venv/bin/activate

You should see your shell prompt change to have the "venv" prefix.

Step 4: install git-buildpackage
--------------------------------

Before going further, the git-buildpackage dependency requires special
handling. New versions (0.9 and newer) no longer support Python 2. It is best
if you install the version that is present in the Xenial distribution. To do
that, use the ``install.sh`` script that Travis CI uses, and set the
``GIT_BUILDPACKAGE_SOURCE`` environment variable::

    GIT_BUILDPACKAGE_SOURCE=xenial ./travisci/install.sh

(We use Travis CI to test rhcephpkg against a matrix of different Python
versions and git-buildpackage releases. This is why ``setup.py`` does not
explicitly pin ``git-buildpackage``.)

Step 5: install rhcephpkg
-------------------------

This is pretty standard for any Python application that you want to hack on::

    python setup.py develop

At this point you can run ``which rhcephpkg`` to verify that you're using the
one from your virtualenv, and ensure that a simple help command works::

    rhcephpkg --help

You can now test your feature from Git.

More tips for working in the virtualenv
---------------------------------------

Due to the way ``setup.py develop`` works, you can make changes in Git, or
switch branches, etc. and your changes will be immediately "live" when you run
the ``rhcephpkg`` command.

If you change the version number (in ``rhcephpkg/__init__.py``), the setuptools
``bin/rhcephpkg`` stub will no longer be able to locate the rhcephpkg source
code, so you'll need to run ``python setup.py develop`` again to update the
virtualenv's egg link. The version number on rhcephpkg's master branch changes
regularly as we release new versions, so you might experience this problem if
you are trying a much older Git branch with a different version number.
``python setup.py develop`` and all will be well again.


Developing on Fedora
====================

Now that the `devscripts package
<https://apps.fedoraproject.org/packages/devscripts>`_ is available in Fedora,
it is possible to run many rhcephpkg commands on a Fedora system, without
having to use an Ubuntu environment.

::

    sudo dnf install devscripts python-virtualenv
    ...

For example ``rhcephpkg clone`` or ``rhcephpkg build`` work fine directly on
Fedora when running within a virtualenv. The test suite should also pass on
Fedora as well.

This can save time and effort, because you do not have to use an Ubuntu VM or
container to hack on rhcephpkg or even use it every day.

Some commands do depend on an Ubuntu environment. For example, ``rhcephpkg
localbuild`` needs pbuilder, and pbuilder on Fedora is not available or
well-tested.


References
==========

It is helpful to have a basic understanding of Debian packaging. This document
is a useful primer, but it's detailed, so even skimming is helpful:
https://www.debian.org/doc/manuals/maint-guide/

The git-buildpackage documentation is also very helpful:
https://honk.sigxcpu.org/piki/projects/git-buildpackage/

Guido Günther is very responsive on the git-buildpackage mailing list:
http://lists.sigxcpu.org/mailman/listinfo/git-buildpackage
