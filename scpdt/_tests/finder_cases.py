"""
A set of simple cases for DocTestFinder / DTFinder and its helpers.



1. There is a doctest in the module docstring

>>> 1 + 2
3
"""

__all__ = ['func', 'Klass']


def func():
    """Two doctests in a module-level function.

    >>> 1 + 3
    4

    >>> 5 + 6
    11
    """
    pass


class Klass:
    """A class has doctests in a class docstring.

    >>> 1 + 8
    9
    """
    def meth(self):
        """And a method has its doctests.

        >>> 2 + 11
        13
        """
        pass

    def meth_2(self):
        """
        One other method.

        >>> 111 + 1
        112
        """


def private_func():
    """A non-public function (not listed in __all__) also has examples.

    >>> 9 + 11
    20
    """


def _underscored_private_func():
    """A private function (starts with an undescore) also has examples.

    >>> 9 + 12
    21
    """


