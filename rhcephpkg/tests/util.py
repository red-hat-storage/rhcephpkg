import errno
from io import StringIO
import os
import subprocess
import six
from six.moves.urllib.parse import urlparse
from six.moves.http_client import HTTPMessage
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import urlopen

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


class CallRecorder(object):
    """ Simple recorder for monkeypatching. """
    def __init__(self):
        self.called = 0

    def __call__(self, *args, **kwargs):
        self.called += 1
        try:
            self.args = args[0]
        except IndexError:
            self.args = args


def fake_urlopen(req, **kw):
    """
    Behave like six.moves.urllib.request.urlopen().

    Return the contents of local fixture files on disk instead.
    """
    o = urlparse(req.get_full_url())
    localfile = os.path.join(FIXTURES_DIR, o.netloc, o.path[1:])
    # Try reading the file, and handle some special cases if we get an error.
    try:
        with open(localfile):
            pass
    except IOError as e:
        # Raise HTTP 404 errors for non-existent files.
        if e.errno == errno.ENOENT:
            url = req.get_full_url()
            headers = HTTPMessage(StringIO(u''))
            raise HTTPError(url, 404, 'Not Found', headers, None)
        # If URL looked like a directory ("/"), open the file instead.
        elif e.errno == errno.ENOTDIR:
            localfile = localfile.rstrip('/')
        # If localfile's a directory, look for a matching ".body" file instead.
        elif e.errno == errno.EISDIR:
            localfile = localfile.rstrip('/') + '.body'
        else:
            raise

    response = urlopen('file://' + localfile)

    return response


def git(*args):
    """ shortcut for shelling out to git """
    cmd = ['git'] + list(args)
    output = subprocess.check_output(cmd)
    if six.PY3:
        return output.decode('utf-8').rstrip()
    return output.rstrip()
