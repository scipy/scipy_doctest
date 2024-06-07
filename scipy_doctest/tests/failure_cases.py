__all__ = ['func9', 'func10', 'iterable_length_1', 'iterable_length_2',
           'different_iteralbes_1', 'different_iteralbes_2']


def func9():
    """
    Wrong output.
    >>> import numpy as np
    >>> np.array([1, 2, 3])
    array([2, 3, 4])
    """


def func10():
    """
    NameError
    >>> import numpy as np
    >>> np.arraY([1, 2, 3])
    """


def iterable_length_1():
    """
    >>> [1, 2, 3]
    [1, 2, 3, 4]
    """


def iterable_length_2():
    """
    >>> [1, 2, 3]
    [1, 2]
    """


def different_iteralbes_1():
    """
    >>> [0, 1, 2]
    (0, 1, 2)
    """


def different_iteralbes_2():
    """
    >>> import numpy as np
    >>> np.array([0, 1, 2])
    [0, 1, 2]
    """
