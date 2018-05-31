import pytest
import rhcephpkg.changelog as changelog


@pytest.fixture(autouse=True)
def pkgdir(tmpdir, monkeypatch):
    """
    temp directory fixture containing a readable/writable ./debian/changelog.
    """
    cfile = tmpdir.mkdir('debian').join('changelog')
    text = """
testpkg (1.1.0-1) stable; urgency=medium

  * update to 1.1.0
  * other rad packaging updates
  * even more cool packaging updates that take a lot of text to describe so
    the change wraps on multiple lines

 -- Ken Dreyer <kdreyer@redhat.com>  Tue, 06 Jun 2017 14:46:37 -0600

testpkg (1.0.0-2redhat1) stable; urgency=medium

  * update to 1.0.0 (rhbz#123)

 -- Ken Dreyer <kdreyer@redhat.com>  Mon, 05 Jun 2017 13:45:36 -0600
""".lstrip("\n")
    cfile.write(text)
    monkeypatch.chdir(tmpdir)
    return tmpdir


def test_distribution():
    assert changelog.distribution() == 'stable'


def test_changes_string():
    expected = """
   * update to 1.1.0
   * other rad packaging updates
   * even more cool packaging updates that take a lot of text to describe so
     the change wraps on multiple lines
""".strip("\n")
    assert changelog.changes_string() == expected


def test_changes_iterator():
    itrator = changelog.changes_iterator()
    assert next(itrator) == 'update to 1.1.0'
    assert next(itrator) == 'other rad packaging updates'


def test_list_changes():
    expected = [
        'update to 1.1.0',
        'other rad packaging updates',
        'even more cool packaging updates that take a lot of text to describe so the change wraps on multiple lines',  # noqa E510
    ]
    assert changelog.list_changes() == expected
