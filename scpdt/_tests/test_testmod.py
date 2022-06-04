import io
from contextlib import redirect_stderr

import numpy as np
import pytest
import doctest

from . import (module_cases as module,
               stopwords_cases as stopwords,
               finder_cases,
               failure_cases)
from .._run import testmod, find_doctests
from .._checker import DTConfig

_VERBOSE = 2


def test():
    test_module()
    test_module_vanilla_dtfinder()
    test_stopwords()


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
    res, _ = testmod(module, verbose=_VERBOSE, strategy='public')
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_public_obj failed.")
    return res


def test_explicit_object_list():
    objs = [finder_cases.Klass]
    tests = find_doctests(finder_cases, strategy=objs)
    assert [test.name for test in tests] == ['Klass', 'Klass.meth']


def test_explicit_object_list_with_module():
    # Module docstrings are examined literally, without looking into other objects
    # in the module. These other objects need to be listed explicitly.
    # In the `doctest`-speak: do not recurse.
    objs = [finder_cases, finder_cases.Klass]
    tests = find_doctests(finder_cases, strategy=objs)
    assert ([test.name for test in tests] ==
            ['scpdt._tests.finder_cases', 'Klass', 'Klass.meth'])


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
