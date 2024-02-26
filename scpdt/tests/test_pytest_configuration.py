import pytest
from pathlib import PosixPath, Path

from . import module_cases, failure_cases, failure_cases_2, stopwords_cases, local_file_cases
from scpdt.conftest import dt_config

# XXX: this is a bit hacky and repetetive. Can rework?


pytest_plugins = ['pytester']


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
    

def test_stopword_cases(pytester):
    """Test that pytest uses the DTParser for doctests."""
    path_str = stopwords_cases.__file__
    python_file = PosixPath(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK


def test_local_file_cases(pytester):
    """Test that local files are found for use in doctests.
    """
    path_str = local_file_cases.__file__
    python_file = PosixPath(path_str)
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK
