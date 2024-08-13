from ..conftest import dt_config

# Specify local files required by doctests
dt_config.local_resources = {
    'scipy_doctest.tests.local_file_cases.local_files': ['local_file.txt'],
    'scipy_doctest.tests.local_file_cases.sio': ['octave_a.mat']
}


__all__ = ['local_files', 'sio']


def local_files():
    """
    A doctest that tries to read a local file

    >>> with open('local_file.txt', 'r'):
    ...     pass
    """


def sio():
    """
    The .mat file is from scipy/tutorial/io.rst; The test checks that a want/got
    being a dict is handled correctly.

    >>> import scipy.io as sio
    >>> sio.loadmat('octave_a.mat')
    {'__header__': b'MATLAB 5.0 MAT-file, written by Octave 3.2.3, 2010-05-30 02:13:40 UTC',
     '__version__': '1.0',
     '__globals__': [],
     'a': array([[[ 1.,  4.,  7., 10.],
                  [ 2.,  5.,  8., 11.],
                  [ 3.,  6.,  9., 12.]]])}
    """


