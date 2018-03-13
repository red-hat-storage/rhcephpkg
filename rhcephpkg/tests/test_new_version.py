import pytest
from rhcephpkg.new_version import NewVersion
from rhcephpkg.tests.util import CallRecorder
from rhcephpkg.tests.util import git


def test_good_gbp_settings(testpkg):
    nv = NewVersion(['rhcephpkg'])
    nv.ensure_gbp_settings()


def test_bad_gbp_pristine_tar(testpkg):
    gbpfile = testpkg.join('debian').join('gbp.conf')
    contents = """
[DEFAULT]
pristine-tar = False
merge-mode = replace
upstream-branch = upstream/ceph-2-ubuntu
"""
    gbpfile.write(contents)
    nv = NewVersion(['rhcephpkg'])
    with pytest.raises(RuntimeError):
        nv.ensure_gbp_settings()


def test_bad_gbp_merge_mode(testpkg):
    gbpfile = testpkg.join('debian').join('gbp.conf')
    contents = """
[DEFAULT]
pristine-tar = True
upstream-branch = upstream/ceph-2-ubuntu
"""
    gbpfile.write(contents)
    nv = NewVersion(['rhcephpkg'])
    with pytest.raises(RuntimeError):
        nv.ensure_gbp_settings()


def test_bad_upstream_branch(testpkg):
    gbpfile = testpkg.join('debian').join('gbp.conf')
    contents = """
[DEFAULT]
pristine-tar = True
merge-mode = replace
"""
    gbpfile.write(contents)
    nv = NewVersion(['rhcephpkg'])
    with pytest.raises(RuntimeError):
        nv.ensure_gbp_settings()


def test_import_orig(monkeypatch):
    recorder = CallRecorder()
    monkeypatch.setattr('subprocess.check_call', recorder)
    nv = NewVersion(['rhcephpkg'])
    nv.import_orig()
    expected = ['gbp', 'import-orig', '--no-interactive', '--uscan']
    assert recorder.args == expected


def test_import_orig_tarball(monkeypatch):
    recorder = CallRecorder()
    monkeypatch.setattr('subprocess.check_call', recorder)
    nv = NewVersion(['rhcephpkg'])
    tarball = 'testpkg_1.0.orig.tar.gz'
    nv.import_orig(tarball)
    expected = ['gbp', 'import-orig', '--no-interactive', tarball]
    assert recorder.args == expected


def test_run_dch(monkeypatch):
    recorder = CallRecorder()
    monkeypatch.setattr('subprocess.check_call', recorder)
    nv = NewVersion(['rhcephpkg'])
    nv.run_dch()
    expected = ['gbp', 'dch', '--auto', '-R', '--spawn-editor=never']
    assert recorder.args == expected


def test_insert_rhbzs(testpkg):
    nv = NewVersion(['rhcephpkg'])
    bugstr = 'rhbz#445566'
    nv.insert_rhbzs(bugstr)
    clog = testpkg.join('debian').join('changelog')
    contents = clog.read()
    expected = """
testpkg (1.0.0-2redhat1) xenial; urgency=low

  * Initial package (rhbz#445566)

 -- Ken Dreyer <kdreyer@redhat.com>  Tue, 06 Jun 2017 14:46:37 -0600
""".lstrip("\n")
    assert contents == expected


def test_commit(testpkg, capfd):
    # replace changelog with new text
    clog = testpkg.join('debian').join('changelog')
    newcontents = """
testpkg (2.0.0-2redhat1) xenial; urgency=low

  * Import Version 2.0.0 (rhbz#567)

 -- Ken Dreyer <kdreyer@redhat.com>  Tue, 06 Jun 2017 14:46:37 -0600
""".lstrip("\n")
    clog.write(newcontents)
    nv = NewVersion(['rhcephpkg'])
    nv.commit()
    nv.show()
    out, _ = capfd.readouterr()
    assert "debian: 2.0.0-2redhat1" in out


def test_main(testpkg, monkeypatch):
    # Fake the "upstream/1.0" tag that `gbp import-orig` would've created:
    git('tag', '-a', 'upstream/1.0', '-m', 'Upstream version 1.0')
    recorder = CallRecorder()
    monkeypatch.setattr('subprocess.check_call', recorder)
    nv = NewVersion(['rhcephpkg'])
    nv.main()
