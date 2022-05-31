import pytest

from . import failure_cases as module
from .. import DTFinder, DTRunner


### Smoke test DTRunner methods. Mainly to check that they are runnable.

def test_single_failure():
    finder = DTFinder()
    tests = finder.find(module.func9)
    runner = DTRunner(verbose=True)
    for test in tests:
        runner.run(test)

  
