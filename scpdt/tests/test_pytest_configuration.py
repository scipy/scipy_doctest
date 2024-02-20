import pytest
import os
from pathlib import PosixPath, Path

from . import module_cases, failure_cases, failure_cases_2, stopwords_cases, local_file_cases
from scpdt.plugin import copy_local_files
from scpdt.conftest import dt_config

pytest_plugins = ['pytester']


@pytest.fixture(autouse=True)
def copy_files():
    """
    Copy necessary local files for doctests to the temporary directory used by pytester. 
    The files to be copied are defined by the `local_resources` attribute of a DTConfig instance.
    When testing is done, all copied files are deleted.
    """
    try:
        dirname = os.path.dirname(Path(__file__))

        # Update the file path of each filename
        for value in dt_config.local_resources.values():
            for i, path in enumerate(value):
                value[i] = os.path.join(dirname, os.path.basename(path))

        # Copy the files
        copied_files = copy_local_files(dt_config.local_resources, os.getcwd())

        yield copied_files

    finally:
        # Perform clean-up
        for filepath in copied_files:
            try:
                os.remove(filepath)
            except FileNotFoundError:
                pass


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
    """Test that local files are found for use in doctests."""
    path_str = local_file_cases.__file__
    python_file = PosixPath(path_str)
    assert python_file is None
    result = pytester.inline_run(python_file, "--doctest-modules")
    assert result.ret == pytest.ExitCode.OK
