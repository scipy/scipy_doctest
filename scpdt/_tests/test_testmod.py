import io
from contextlib import redirect_stderr

import numpy as np
import pytest
import doctest

from . import (module_cases as module,
               stopwords_cases as stopwords,
               finder_cases,
               failure_cases,
               failure_cases_2)
from .._frontend import testmod, find_doctests, run_docstring_examples
from .._util import warnings_errors
from .._impl import DTConfig

_VERBOSE = 2


def test_module():
    res, _ = testmod(module, verbose=_VERBOSE)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_module(DTFinder) failed)")
    return res


def test_module_vanilla_dtfinder():
    config = DTConfig()
    config.stopwords = []
    res, _ = testmod(module, verbose=_VERBOSE, config=config)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_module(vanilla DocTestFinder) failed)")
    return res


def test_stopwords():
    res, _ = testmod(stopwords, verbose=_VERBOSE)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_stopwords failed.")
    return res


def test_public_obj_discovery():
    res, _ = testmod(module, verbose=_VERBOSE, strategy='api')
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_public_obj failed.")
    return res


def test_explicit_object_list():
    objs = [finder_cases.Klass]
    tests = find_doctests(finder_cases, strategy=objs)

    base = 'scpdt._tests.finder_cases'
    assert ([test.name for test in tests] ==
            [base + '.Klass', base + '.Klass.meth'])


def test_explicit_object_list_with_module():
    # Module docstrings are examined literally, without looking into other objects
    # in the module. These other objects need to be listed explicitly.
    # In the `doctest`-speak: do not recurse.
    objs = [finder_cases, finder_cases.Klass]
    tests = find_doctests(finder_cases, strategy=objs)

    base = 'scpdt._tests.finder_cases'
    assert ([test.name for test in tests] ==
            [base, base + '.Klass', base + '.Klass.meth'])


def test_run_docstring_examples():
    f = finder_cases.Klass
    res1 = run_docstring_examples(f)
    res2 = testmod(finder_cases, strategy=[finder_cases.Klass])
    assert res1 == res2


def test_global_state():
    # Make sure doctesting does not alter the global state, as much as reasonable
    objs = [module.manip_printoptions]
    opts = np.get_printoptions()
    testmod(module)
    new_opts = np.get_printoptions()
    assert new_opts == opts


def test_module_debugrunner():
    with pytest.raises((doctest.UnexpectedException, doctest.DocTestFailure)):
        res = testmod(failure_cases, raise_on_error=True)


def test_verbosity_1():
    # smoke test that verbose=1 works
    stream = io.StringIO()
    with redirect_stderr(stream):
        testmod(failure_cases, verbose=1, report=False)


def test_user_context():
    # use a user context to turn warnings to errors : test that it raises
    config = DTConfig()
    config.user_context_mgr = warnings_errors
    with pytest.raises(doctest.UnexpectedException):
        testmod(failure_cases_2,
                raise_on_error=True, strategy=[failure_cases_2.func_depr],
                config=config)


class TestNameErrorAfterException:
    def test_name_error_after_exception(self):
        # After an example fails, subsequent examples may emit NameErrors.
        # Check that they are suppressed.
        # This first came in in https://github.com/scipy/scipy/pull/13116
        stream = io.StringIO()
        with redirect_stderr(stream):
            testmod(failure_cases_2,
                    strategy=[failure_cases_2.func_name_error])

        stream.seek(0)
        output = stream.read()

        assert "ValueError:" in output   # the original exception
        assert "NameError:" not in output  # the follow-up NameError

    def test_name_error_after_exception_off(self):
        # show NameErrors
        config = DTConfig(nameerror_after_exception=True)
        stream = io.StringIO()
        with redirect_stderr(stream):
            testmod(failure_cases_2,
                    strategy=[failure_cases_2.func_name_error], config=config)

        stream.seek(0)
        output = stream.read()

        assert "ValueError:" in output   # the original exception
        assert "NameError:" in output    # the follow-up NameError
