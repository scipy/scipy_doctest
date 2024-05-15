"""
Doctests on steroids.

Whitespace-insensitive, numpy-aware, floating-point-aware doctest helpers.
"""


__version__ = "1.2dev0"

from .impl import DTChecker, DTFinder, DTParser, DTRunner, DebugDTRunner, DTConfig  # noqa
from .frontend import testmod, testfile, find_doctests, run_docstring_examples      # noqa

