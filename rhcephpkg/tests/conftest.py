import os
import pytest
import py.path
import subprocess


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


@pytest.fixture(autouse=True)
def fake_home(monkeypatch):
    monkeypatch.setenv('HOME', FIXTURES_DIR)


@pytest.fixture
def testpkg(tmpdir, monkeypatch):
    """ Set up a minimal testpkg Git repository and chdir into it. """
    fdir = py.path.local(FIXTURES_DIR)
    dest = tmpdir.mkdir('testpkg')
    fdir.join('testpkg').copy(dest)
    monkeypatch.chdir(dest)
    commands = [
        ['git', 'init', '-q'],
        ['git', 'config', 'user.name', 'Test User'],
        ['git', 'config', 'user.email', 'test@example.com'],
        ['git', 'add', '*'],
        ['git', 'commit', '-q', '-m', 'initial import'],
        ['git', 'branch', '-m', 'ceph-2-ubuntu'],
        ['git', 'branch', 'patch-queue/ceph-2-ubuntu'],
    ]
    for c in commands:
        subprocess.check_call(c)
    return dest
