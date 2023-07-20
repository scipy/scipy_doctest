import pytest

pytest_plugins = ['pytester']

def test_array_abbreviation(pytester):
    """
    Test that pytest uses the DTChecker that handles array abbreviation
    """

    file_content = """
    def array_abbreviation():
        '''
        >>> import numpy as np    
        >>> np.diag(np.arange(33)) / 30
        array([[0., 0., 0., ..., 0., 0.,0.],
            [0., 0.03333333, 0., ..., 0., 0., 0.],
            [0., 0., 0.06666667, ..., 0., 0., 0.],
            ...,
            [0., 0., 0., ..., 1., 0., 0.],
            [0., 0., 0., ..., 0., 1.03333333, 0.],
            [0., 0., 0., ..., 0., 0., 1.06666667]])
        '''
        pass
        """
    pytester.makepyfile(file_content)

    result = pytester.runpytest("--doctest-modules")
    
    assert result.ret == pytest.ExitCode.OK