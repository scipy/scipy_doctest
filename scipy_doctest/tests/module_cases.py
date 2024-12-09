__all__ = [
    'func', 'func2', 'func3', 'func4', 'func5', 'func6', 'func8',
    'func7', 'manip_printoptions', 'array_abbreviation'
]

import numpy as np
import pytest

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
    >>> import numpy as np
    >>> np.array([1,         2,          3.0])
    array([1, 2, 3])

    Check that the comparison is with atol and rtol: give less digits than
    what numpy by default prints
    >>> np.sin([1., 2, 3])
    array([0.8414, 0.9092, 0.1411])

    Also check that numpy repr for e.g. dtypes is recognized
    >>> np.array([1, 2, 3], dtype=np.float32)
    array([1., 2., 3.], dtype=float32)

    """


def func3():
    """
    Check that printed arrays are checked with atol/rtol
    >>> import numpy as np
    >>> a = np.array([1, 2, 3, 4]) / 3
    >>> print(a)
    [0.33  0.66  1  1.33]
    """


def func_printed_arrays():
    """
    Check various ways handling of printed arrays can go wrong.

    >>> import numpy as np
    >>> a = np.arange(8).reshape(2, 4) / 3
    >>> print(a)  # numpy 1.26.4
    [[0.         0.33333333 0.66666667 1.        ]
     [1.33333333 1.66666667 2.         2.33333333]]

    >>> print(a)   # add spaces (older repr?)
    [[ 0.         0.33333333 0.66666667 1.         ]
     [ 1.33333333 1.66666667 2.         2.33333333 ]]

    Also check 1D arrays
    >>> a1 = np.arange(3)
    >>> print(a1)
    [0 1 2]
    >>> print(a1)
    [ 0 1 2]
    >>> print(a1)
    [ 0 1 2 ]

    """


def func4():
    """
    Test `# may vary` markers : these should not break doctests (but the code
    should still be valid, otherwise it's an error).
    >>> import numpy as np
    >>> np.random.randint(50)
    42      # may vary

    >>> np.random.randint(50)
    42      # Random

    >>> np.random.randint(50)
    42      # random
    """


def func5():
    """
    Object addresses are ignored:
    >>> import numpy as np
    >>> np.array([1, 2, 3]).data
    <memory at 0x7f119b952400>
    """


def func6():
    """
    Masked arrays

    >>> import numpy.ma as ma
    >>> y = ma.array([1, 2, 3], mask = [0, 1, 0])
    >>> y
    masked_array(data=[1, --, 3],
                 mask=[False,  True, False],
           fill_value=999999)

    """


def func8():
    """
    Namedtuples (they are *not* in the namespace)

    >>> from scipy.stats import levene
    >>> a = [8.88, 9.12, 9.04, 8.98, 9.00, 9.08, 9.01, 8.85, 9.06, 8.99]
    >>> b = [8.88, 8.95, 9.29, 9.44, 9.15, 9.58, 8.36, 9.18, 8.67, 9.05]
    >>> c = [8.95, 9.12, 8.95, 8.85, 9.03, 8.84, 9.07, 8.98, 8.86, 8.98]

    # namedtuples are recognized...
    >>> levene(a, b, c)
    LeveneResult(statistic=7.58495, pvalue=0.00243)

    # can be reformatted
    >>> levene(a, b, c)
    LeveneResult(statistic=7.58495,
                 pvalue=0.00243)

    # ... or can be given just as tuples
    >>> levene(a, b, c)
    (7.58495, 0.00243)

    """


def func7():
    """
    Multiline namedtuples + nested tuples, see scipy/gh-16082

    >>> from scipy import stats
    >>> import numpy as np
    >>> a = np.arange(10)
    >>> stats.describe(a)
    DescribeResult(nobs=10, minmax=(0, 9), mean=4.5,
                   variance=9.16666666666, skewness=0.0,
                   kurtosis=-1.224242424)

    A single-line form of a namedtuple
    >>> stats.describe(a)
    DescribeResult(nobs=10, minmax=(0, 9),      mean=4.5,       variance=9.16666, skewness=0.0, kurtosis=-1.2242424)

    """


def manip_printoptions():
    """Manipulate np.printoptions.
    >>> import numpy as np
    >>> np.set_printoptions(linewidth=146)
    """


def array_abbreviation():
    """
    Numpy abbreviates arrays, check that it works.

    XXX: check if ... creates ragged arrays, avoid if so.

    NumPy 2.2 abbreviations
    =======================

    NumPy 2.2 adds shape=(...) to abbreviated arrays.

    This is not a valid argument to `array(...), so it cannot be eval-ed,
    and need to be removed for doctesting.

    The implementation handles both formats, and checks the shapes if present
    in the actual output. If not present in the output, they are ignored.

    >>> import numpy as np
    >>> np.arange(10000)
    array([0, 1, 2, ..., 9997, 9998, 9999], shape=(10000,))

    >>> np.arange(10000, dtype=np.uint16)
    array([   0,    1,    2, ..., 9997, 9998, 9999], shape=(10000,), dtype=uint16)

    >>> np.diag(np.arange(33)) / 30
    array([[0., 0., 0., ..., 0., 0.,0.],
           [0., 0.03333333, 0., ..., 0., 0., 0.],
           [0., 0., 0.06666667, ..., 0., 0., 0.],
           ...,
           [0., 0., 0., ..., 1., 0., 0.],
           [0., 0., 0., ..., 0., 1.03333333, 0.],
           [0., 0., 0., ..., 0., 0., 1.06666667]], shape=(33, 33))


    >>> np.diag(np.arange(1, 1001, dtype=np.uint16))
    array([[1,    0,    0, ...,    0,    0,    0],
           [0,    2,    0, ...,    0,    0,    0],
           [0,    0,    3, ...,    0,    0,    0],
            ...,
           [0,    0,    0, ...,  998,    0,    0],
           [0,    0,    0, ...,    0,  999,    0],
           [0,    0,    0, ...,    0,    0, 1000]], shape=(1000, 1000), dtype=uint16)
    """


def nan_equal():
    """
    Test that nans are treated as equal.

    >>> import numpy as np
    >>> np.nan
    np.float64(nan)
    """


def test_cmplx_nan():
    """
    Complex nans
    >>> import numpy as np
    >>> np.nan - 1j*np.nan
    nan + nanj

    >>> np.nan + 1j*np.nan
    np.complex128(nan+nanj)

    >>> 1j*np.complex128(np.nan)
    np.complex128(nan+nanj)
    """


def array_and_list_1():
    """
    >>> import numpy as np
    >>> np.array([1, 2, 3])
    [1, 2, 3]
    """


def array_and_list_2():
    """
    >>> import numpy as np
    >>> [1, 2, 3]
    array([1, 2, 3])
    """
