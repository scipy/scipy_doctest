import io

import pytest

from . import failure_cases as module
from .. import DTFinder, DTRunner


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
        runner.run(test, out = stream.write)

    stream.seek(0)
    output = stream.read()
    assert output.startswith('\n func10\n ------\n')

