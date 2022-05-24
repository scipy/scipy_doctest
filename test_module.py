def func():
    """
    >>> 2 / 3
    0.667
    """
    pass


def func2():
    """
    Check that `np.` is imported and the array repr is recognized. Also check
    that whitespace is irrelevant for the checker.
    >>> np.array([1,         2,          3.0])
    array([1, 2, 3])

    Check that the comparison is with atol and rtol: give less digits than
    what numpy by default prints  
    >>> np.sin([1., 2, 3])
    array([0.8414, 0.9092, 0.1411])
    """

def func3():
    """
    Check that printed arrays are checked with atol/rtol
    >>> a = np.array([1, 2, 3, 4]) / 3
    >>> print(a)
    [0.33  0.66  1  1.33]
    """

