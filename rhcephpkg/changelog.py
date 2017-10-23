import os
import shutil
import tempfile
from gbp.deb.changelog import ChangeLog
# TODO: move format_changelog method here, and rename to "format_changes".
from rhcephpkg.util import format_changelog


def changes_string():
    """
    Return the "Changes" (bulleted entries) from our most recent
    debian/changelog entry.

    :returns: single indented/bulleted/wrapped ``str``
    """
    clog = ChangeLog(filename='debian/changelog')
    # clog['Changes'] is from dpkg-parsechangelog.
    # First line is the section headers, and we're searching for the blank " ."
    # line after that one:
    section = clog['Changes'].find(" .\n")
    # Note: dpkg-parsechangelog (and therefore git-buildpackage) prefixes each
    # line here with an extraneous space (" ") that is not present in the
    # changelog file itself. Maybe we should dedent this string by one column
    # to be fully accurate? Python's textwrap's dedent can't do this trivially
    # so I'm kicking this down the road for now.
    return clog['Changes'][section+3:]


def changes_iterator():
    """
    Iterate over "Changes" (bulleted entries) in our most recent
    debian/changelog entry.

    :returns: an iterator that yields an unwrapped string for each changelog
              bullet.
    """
    change = ''
    for line in changes_string().splitlines():
        line = line.strip()
        # New "changes" are marked with an asterisk.
        if line.startswith('* '):
            line = line[2:]
            if change:
                yield change
                change = ''
        if change == '':
            change = line
        else:
            change = '%s %s' % (change, line)
    yield change


def list_changes():
    """
    Return a list of "Changes" (bulleted entries) in our most recent
    debian/changelog entry.

    :returns: list of unwrapped strings, one per bullet ("*")
    """
    return list(changes_iterator())


def replace_changes(changes):
    """
    Replace the current changes with the new ones in the most recent
    debian/changelog entry.

    :param changes: ``list`` of changes (strings)
    """
    old = open('debian/changelog', 'r')
    temp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    # Write the first two lines as-is.
    temp.write(old.readline())  # version header line
    temp.write(old.readline())  # empty line
    # Insert wrapped changelog entries here.
    temp.write(format_changelog(changes))
    # Skip everyting up to the next blank line.
    while old.readline() != "\n":
        pass
    temp.write("\n")  # retore the empty line we just skipped
    shutil.copyfileobj(old, temp)
    temp.close()
    old.close()
    os.rename(temp.name, 'debian/changelog')


def replace_release(release):
    """
    Replace the latest "release" value in a debian/changelog file.

    "debian_version"
    """
    clog = ChangeLog(filename='debian/changelog')
    oldstr = '%s (%s) ' % (clog.name, clog.version)
    tmpl = '{name} ({upstream_version}-{debian_version}) '
    newstr = tmpl.format(name=clog.name,
                         upstream_version=clog.upstream_version,
                         debian_version=release)
    old = open('debian/changelog', 'r')
    temp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    oldheader = old.readline()  # old version header line
    newheader = oldheader.replace(oldstr, newstr)
    temp.write(newheader)
    shutil.copyfileobj(old, temp)
    temp.close()
    old.close()
    os.rename(temp.name, 'debian/changelog')


def git_commit_message():
    """
    Return a Git commit message string from the most recent debian/changelog
    entry.
    """
    clog = ChangeLog(filename='debian/changelog')
    template = """
debian: {version}

{changes}
""".lstrip("\n")
    return template.format(version=clog.version, changes=changes_string())
