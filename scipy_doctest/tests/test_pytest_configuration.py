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


def test_alt_checker_doctestplus(pytester):
    """Test an alternative Checker, from pytest-doctestplus."""
    pytest.importorskip("pytest_doctestplus")

    # create a temporary conftest.py file
    pytester.makeconftest(
        """
        import doctest
        from scipy_doctest.conftest import dt_config

        # hack!
        from pytest_doctestplus.output_checker import OutputChecker as _OutputCheckerImpl

        # DTChecker expectes a `config` ctor argument, add it
        class PDPChecker(_OutputCheckerImpl):
            def __init__(self, config):
                super().__init__()

        # Register the checker
        dt_config.CheckerKlass = PDPChecker
        """
    )

    # create a temporary pytest test file
    src = (
        """
        def func():
            '''
            The doctest below, when run from the command line,
            - passes with `pytest --doctest-modules --doctest-plus`, and
            - fails without `--doctest-plus`.

            We however run this doctest using the PDPChecker, so it picks up
            the FLOAT_CMP directive from doctestplus without a command-line switch.

            >>> 2/3       # doctest: +FLOAT_CMP
            0.666666
            '''
            pass
        """
    )

    # run the doctest
    f = pytester.makepyfile(src)
    result = pytester.inline_run(f, '--doctest-modules')
    assert result.ret == pytest.ExitCode.OK

    # remove the directive and rerun
    src_ = src.replace("# doctest: +FLOAT_CMP", "")
    f_ = pytester.makepyfile(src_)
    result = pytester.inline_run(f_, '--doctest-modules')
    assert result.ret == pytest.ExitCode.TESTS_FAILED
