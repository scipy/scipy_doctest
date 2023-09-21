__all__ = ['func_depr', 'func_name_error']

def func_depr():
    """
    A test case for the user context mgr to turn warnings to errors.

    >>> import warnings; warnings.warn('Sample deprecation warning', DeprecationWarning)
    """


def func_name_error():
    """After an example fails, next examples may emit NameErrors. Suppress them.

    Note that the suppresion is in effect for the duration of the DocTest, i.e.
    for the whole docstring. Maybe this can be fixed at some point.

    >>> def func():
    ...     raise ValueError("oops")
    ...     return 42
    >>> res = func()
    >>> res
    >>> raise NameError('This is legitimate, but is suppressed')

    Further name errors are also suppressed (which is a bug, too):
    >>> raise NameError('Also legit')
    """

