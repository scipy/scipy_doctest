import pytest
from pathlib import PosixPath

from . import module_cases, failure_cases, failure_cases_2, stopwords_cases, local_file_cases


# XXX: this is a bit hacky and repetetive. Can rework?


pytest_plugins = ['pytester']


try:
    import scipy    # noqa
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

try:
    import matplotlib    # noqa
    HAVE_MATPLOTLIB = True
except Exception:
    HAVE_MATPLOTLIB  = False


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_module_cases(pytester):
    """Test that pytest uses the DTChecker for doctests."""
    path_str = module_cases.__file__
    python_file = PosixPath(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


def test_failure_cases(pytester):
    file_list = [failure_cases, failure_cases_2]
    for file in file_list:
        path_str = file.__file__
        python_file = PosixPath(path_str)
        result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    

@pytest.mark.skipif(not HAVE_MATPLOTLIB, reason='need matplotlib')
def test_stopword_cases(pytester):
    """Test that pytest uses the DTParser for doctests."""
    path_str = stopwords_cases.__file__
    python_file = PosixPath(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_local_file_cases(pytester):
    """Test that local files are found for use in doctests.
    """
    path_str = local_file_cases.__file__
    python_file = PosixPath(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK
