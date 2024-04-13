import io

import doctest

import pytest

from . import (failure_cases as module,
               finder_cases as finder_module,
               module_cases)
from .. import DTFinder, DTRunner, DebugDTRunner, DTConfig


### Smoke test DTRunner methods. Mainly to check that they are runnable.

def test_single_failure():
    finder = DTFinder()
    tests = finder.find(module.func9)
    runner = DTRunner(verbose=False)
    stream = io.StringIO()
    for test in tests:
        runner.run(test, out=stream.write)

    stream.seek(0)
    output = stream.read()
    assert output.startswith('\n func9\n -----\n')


def test_exception():
    finder = DTFinder()
    tests = finder.find(module.func10)
    runner = DTRunner(verbose=False)
    stream = io.StringIO()
    for test in tests:
        runner.run(test, out=stream.write)

    stream.seek(0)
    output = stream.read()
    assert output.startswith('\n func10\n ------\n')


def test_get_history():
    finder = DTFinder()
    tests = finder.find(finder_module)
    runner = DTRunner(verbose=False)
    for test in tests:
        runner.run(test)

    dct = runner.get_history()
    assert len(dct) == 7


class TestDebugDTRunner:
    def test_debug_runner_failure(self):
        finder = DTFinder()
        tests = finder.find(module.func9)
        runner = DebugDTRunner(verbose=False)

        with pytest.raises(doctest.DocTestFailure) as exc:
            for t in tests:
                runner.run(t)

        # pytest wraps the original exception, unwrap it
        orig_exception = exc.value

        # DocTestFailure carries the doctest and the run result
        assert orig_exception.test is tests[0]
        assert orig_exception.test.name == 'func9'
        assert orig_exception.got == 'array([1, 2, 3])\n'
        assert orig_exception.example.want == 'array([2, 3, 4])\n'

    def test_debug_runner_exception(self):
        finder = DTFinder()
        tests = finder.find(module.func10)
        runner = DebugDTRunner(verbose=False)

        with pytest.raises(doctest.UnexpectedException) as exc:
            for t in tests:
                runner.run(t)
        orig_exception = exc.value

        # exception carries the original test
        assert orig_exception.test is tests[0]


class VanillaOutputChecker(doctest.OutputChecker):
    """doctest.OutputChecker to drop in for DTChecker.

    LSP break: OutputChecker does not have __init__,
    here we add it to agree with DTChecker.
    """
    def __init__(self, config):
        pass

class TestCheckerDropIn:
    """Test DTChecker and vanilla doctest OutputChecker being drop-in replacements.
    """
    def test_vanilla_checker(self):
        config = DTConfig(CheckerKlass=VanillaOutputChecker)
        runner = DebugDTRunner(config=config)
        tests = DTFinder().find(module_cases.func)

        with pytest.raises(doctest.DocTestFailure):
            for t in tests:
                runner.run(t)

