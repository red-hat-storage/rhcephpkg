import os
from .log import log
from .build import Build
from .checkout_from_patches import CheckoutFromPatches
from .clone import Clone
from .download import Download
from .gitbz import Gitbz
from .hello import Hello
from .list_builds import ListBuilds
from .localbuild import Localbuild
from .merge_patches import MergePatches
from .new_version import NewVersion
from .patch import Patch
from .source import Source
from .watch_build import WatchBuild

__all__ = ['log', 'Build', 'CheckoutFromPatches', 'Clone', 'Download',
           'Gitbz', 'Hello', 'ListBuilds', 'Localbuild', 'MergePatches',
           'NewVersion', 'Patch', 'Source', 'WatchBuild']

__version__ = '1.11.0'

# Always use our system-wide certificate store.

# When we're using upstream requests (ie within a virtualenv), we need to point
# at our system bundle that contains the Red Hat CA.

# (This is not necessary when using the python-requests RPM or DEB since that
# already uses the system certificate store.)

if 'REQUESTS_CA_BUNDLE' not in os.environ:
    # RH-based OSes
    if os.path.exists('/etc/pki/tls/certs/ca-bundle.crt'):
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/pki/tls/certs/ca-bundle.crt'
    # Debian-based OSes
    if os.path.exists('/etc/ssl/certs/ca-certificates.crt'):
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
