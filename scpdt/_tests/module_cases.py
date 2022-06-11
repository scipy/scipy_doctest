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

    Also check that numpy repr for e.g. dtypes is recognized
    >>> np.array([1, 2, 3], dtype=np.float32)
    array([1., 2., 3.], dtype=float32)

    """


def func3():
    """
    Check that printed arrays are checked with atol/rtol
    >>> a = np.array([1, 2, 3, 4]) / 3
    >>> print(a)
    [0.33  0.66  1  1.33]
    """


def func4():
    """
    Test `# may vary` markers : these should not break doctests (but the code
    should still be valid, otherwise it's an error).

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

    >>> np.set_printoptions(linewidth=146)
    """
