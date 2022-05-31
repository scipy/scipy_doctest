"""
Doctests on steroids.

Whitespace-insensitive, numpy-aware, floating-point-aware doctest helpers.
"""


__version__ = "0.1"

from ._checker import DTChecker, DTFinder, DTRunner
from ._run import testmod

from ._tests import test

