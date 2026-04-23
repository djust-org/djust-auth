"""
djust-auth — now part of djust.

This package has been folded into djust core. Install djust instead:

    pip install djust

All functionality is now available at djust.auth.
"""
import warnings

warnings.warn(
    "djust-auth is deprecated. Use 'pip install djust' and import "
    "from djust.auth instead. See MIGRATION.md for details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new djust location
from djust.auth import *  # noqa: F401, F403, E402

try:
    from djust.auth import __all__  # noqa: E402, F401
except ImportError:
    __all__ = []

__version__ = "99.0.0"
