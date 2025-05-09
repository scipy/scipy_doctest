__all__ = ['func9', 'func10', 'iterable_length_1', 'iterable_length_2',
           'tuple_and_list_1', 'tuple_and_list_2']


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


def tuple_and_list_1():
    """
    >>> [0, 1, 2]
    (0, 1, 2)
    """


def tuple_and_list_2():
    """
    >>> (0, 1, 2)
    [0, 1, 2]
    """


def dtype_mismatch():
    """
    >>> import numpy as np
    >>> 3.0
    3
    """


def dict_not_dict():
    """
    >>> dict(a=1, b=2)
    ['a', 'b']
    """

def dict_not_dict_2():
    """
    >>> [('a', 1), ('b', 2)]
    {'a': 1, 'b': 2}
    """


def dict_wrong_keys():
    """
    >>> dict(a=1, b=2)
    {'c': 1, 'd': 2}
    """


def dict_wrong_values():
    """
    >>> dict(a=1, b=2)
    {'a': -1, 'b': -2}
    """


def dict_wrong_values_np():
    """
    >>> import numpy as np
    >>> dict(a=1, b=np.arange(3)/3)
    {'a': 1, 'b': array([0, 0.335, 0.669])}
    """


def dict_nested_wrong_values_np():
    """
    >>> import numpy as np
    >>> dict(a=1, b=dict(blurb=np.arange(3)/3))
    {'a': 1, 'b': {'blurb': array([0, 0.335, 0.669])}}
    """
