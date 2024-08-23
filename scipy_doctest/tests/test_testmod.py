import io
import doctest

from contextlib import redirect_stderr

import numpy as np

try:
    import matplotlib.pyplot as plt    # noqa
    HAVE_MATPLOTLIB = True
except Exception:
    HAVE_MATPLOTLIB = False

import pytest

try:
    import scipy    # noqa
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

from . import (module_cases as module,
               stopwords_cases as stopwords,
               finder_cases,
               failure_cases,
               failure_cases_2,
               local_file_cases)
from ..frontend import testmod as _testmod, run_docstring_examples
from ..util import warnings_errors
from ..impl import DTConfig

_VERBOSE = 2


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_module():
    res, _ = _testmod(module, verbose=_VERBOSE)
    assert res.failed == 0
    assert res.attempted != 0


@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_module_vanilla_dtfinder():
    config = DTConfig()
    config.stopwords = []
    res, _ = _testmod(module, verbose=_VERBOSE, config=config)
    assert res.failed == 0
    assert res.attempted != 0


@pytest.mark.skipif(not HAVE_MATPLOTLIB, reason='need matplotlib')
def test_stopwords():
    res, _ = _testmod(stopwords, verbose=_VERBOSE)
    assert res.failed == 0
    assert res.attempted != 0
    

@pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
def test_public_obj_discovery():
    res, _ = _testmod(module, verbose=_VERBOSE, strategy='api')
    assert res.failed == 0
    assert res.attempted != 0


def test_run_docstring_examples():
    f = finder_cases.Klass
    res1 = run_docstring_examples(f)
    res2 = _testmod(finder_cases, strategy=[finder_cases.Klass])
    assert res1 == res2


def test_global_state():
    # Make sure doctesting does not alter the global state, as much as reasonable
    opts = np.get_printoptions()
    _testmod(module)
    new_opts = np.get_printoptions()
    assert new_opts == opts


def test_module_debugrunner():
    with pytest.raises((doctest.UnexpectedException, doctest.DocTestFailure)):
        _testmod(failure_cases, raise_on_error=True)


def test_verbosity_1():
    # smoke test that verbose=1 works
    stream = io.StringIO()
    with redirect_stderr(stream):
        _testmod(failure_cases, verbose=1, report=False)


def test_user_context():
    # use a user context to turn warnings to errors : test that it raises
    config = DTConfig()
    config.user_context_mgr = warnings_errors
    with pytest.raises(doctest.UnexpectedException):
        _testmod(failure_cases_2,
                raise_on_error=True, strategy=[failure_cases_2.func_depr],
                config=config)


def test_wrong_lengths():
    config = DTConfig()
    res, _ = _testmod(failure_cases,
                      strategy=[failure_cases.iterable_length_1,
                                failure_cases.iterable_length_2],
                      config=config)
    assert res.failed == 2


def test_tuple_and_list():
    config = DTConfig()
    res, _ = _testmod(failure_cases,
                      strategy=[failure_cases.tuple_and_list_1,
                                failure_cases.tuple_and_list_2],
                      config=config)
    assert res.failed == 2


@pytest.mark.parametrize('strict, num_fails', [(True, 1), (False, 0)])
class TestStrictDType:
    def test_np_fix(self, strict, num_fails):
        config = DTConfig(strict_check=strict)
        res, _ = _testmod(failure_cases,
                          strategy=[failure_cases.dtype_mismatch],
                          config=config)
        assert res.failed == num_fails


class TestLocalFiles:
    def test_local_files(self):
        # A doctest tries to open a local file. Test that it works
        # (internally, the file will need to be copied).
        config = DTConfig()
        config.local_resources = {'scipy_doctest.tests.local_file_cases.local_files':
                                  ['local_file.txt']}
        res, _ = _testmod(local_file_cases, config=config,
                         strategy=[local_file_cases.local_files],
                         verbose=_VERBOSE)

        assert res.failed == 0
        assert res.attempted != 0

    @pytest.mark.skipif(not HAVE_SCIPY, reason='need scipy')
    def test_sio_octave(self):
        # scipy/tutorial/io.rst : octave_a.mat file
        config = DTConfig()
        config.local_resources = {'scipy_doctest.tests.local_file_cases.sio':
                                  ['octave_a.mat']}
        res, _ = _testmod(local_file_cases, config=config,
                          strategy=[local_file_cases.sio],
                          verbose=_VERBOSE)

        assert res.failed == 0
        assert res.attempted != 0


class TestNameErrorAfterException:
    def test_name_error_after_exception(self):
        # After an example fails, subsequent examples may emit NameErrors.
        # Check that they are suppressed.
        # This first came in in https://github.com/scipy/scipy/pull/13116
        stream = io.StringIO()
        with redirect_stderr(stream):
            _testmod(failure_cases_2,
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
            _testmod(failure_cases_2,
                     strategy=[failure_cases_2.func_name_error], config=config)

        stream.seek(0)
        output = stream.read()

        assert "ValueError:" in output   # the original exception
        assert "NameError:" in output    # the follow-up NameError
