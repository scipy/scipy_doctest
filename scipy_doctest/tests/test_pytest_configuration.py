import pytest

try:
    import matplotlib.pyplot as plt    # noqa
    HAVE_MATPLOTLIB = True
except Exception:
    HAVE_MATPLOTLIB = False

try:
    import scipy    # noqa
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

from pathlib import Path

from . import module_cases, failure_cases, failure_cases_2, stopwords_cases, local_file_cases

# XXX: this is a bit hacky and repetetive. Can rework?


pytest_plugins = ['pytester']


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_module_cases(pytester):
    """Test that pytest uses the DTChecker for doctests."""
    path_str = module_cases.__file__
    python_file = Path(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


def test_failure_cases(pytester):
    file_list = [failure_cases, failure_cases_2]
    for file in file_list:
        path_str = file.__file__
        python_file = Path(path_str)
        result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.TESTS_FAILED

    
@pytest.mark.skipif(not HAVE_MATPLOTLIB, reason='need matplotlib')
def test_stopword_cases(pytester):
    """Test that pytest uses the DTParser for doctests."""
    path_str = stopwords_cases.__file__
    python_file = Path(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_local_file_cases(pytester):
    """Test that local files are found for use in doctests."""
    path_str = local_file_cases.__file__
    python_file = Path(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


def test_alt_checker(pytester):
    """Test an alternative Checker."""

    # create a temporary conftest.py file
    pytester.makeconftest(
        """
        import doctest
        from scipy_doctest.conftest import dt_config

        class Vanilla(doctest.OutputChecker):
            def __init__(self, config):
                pass

        dt_config.CheckerKlass = Vanilla
    """
    )

    # create a temporary pytest test file
    f = pytester.makepyfile(
        """
        def func():
            '''
            >>> 2 / 3     # fails with vanilla doctest.OutputChecker
            0.667
            '''
            pass
    """
    )

    # run all tests with pytest
    result = pytester.inline_run(f, '--doctest-modules')
    assert result.ret == pytest.ExitCode.TESTS_FAILED

