"""
Doctests on steroids.

Whitespace-insensitive, numpy-aware, floating-point-aware doctest helpers.
"""


__version__ = "0.1"

from ._impl import DTChecker, DTFinder, DTRunner, DebugDTRunner, DTConfig
from ._frontend import testmod, find_doctests, run_docstring_examples

from ._tests import test

