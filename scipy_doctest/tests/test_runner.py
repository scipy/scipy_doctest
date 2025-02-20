import io
import doctest
import pytest

try:
    import xdoctest
    HAVE_XDOCTEST = True
except ModuleNotFoundError:
    HAVE_XDOCTEST = False

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
        tests = DTFinder(config=config).find(module_cases.func)

        with pytest.raises(doctest.DocTestFailure):
            for t in tests:
                runner.run(t)


class VanillaParser(doctest.DocTestParser):
    def __init__(self, config):
        self.config = config
        pass


class XDParser(doctest.DocTestParser):
    """ Wrap `xdoctest` parser.
    """
    def __init__(self, config):
        self.config = config
        self.xd = xdoctest.parser.DoctestParser()

    def parse(self, string, name='<string>'):
        return self.xd.parse(string)

    def get_examples(self, string, name='<string>'):
        """
        Similar to doctest.DocTestParser.get_examples, only
        account for the fact that individual examples
        are instances of DoctestPart not doctest.Example
        """
        return [x for x in self.parse(string, name)
                if isinstance(x, xdoctest.doctest_part.DoctestPart)]


class TestParserDropIn:
    """ Test an alternative DoctestParser
    """
    def test_vanilla_parser(self):
        config = DTConfig(ParserKlass=VanillaParser)
        runner = DebugDTRunner(config=config)
        tests = DTFinder(config=config).find(module_cases.func3)

        assert len(tests) == 1
        assert len(tests[0].examples) == 3

    @pytest.mark.skipif(not HAVE_XDOCTEST, reason="needs xdoctest")
    def test_xdoctest_parser(self):
        # Note that the # of examples differ from DTParser:
        # - xdoctest groups doctest lines with no 'want' output into a single
        #   example.
        # - "examples" here are DoctestPart instances, which _almost_ quack
        #    like `doctest.Example` but not completely.
        config = DTConfig(ParserKlass=XDParser)
        runner = DebugDTRunner(config=config)
        tests = DTFinder(config=config).find(module_cases.func3)

        assert len(tests) == 1
        assert len(tests[0].examples) == 2
        assert (tests[0].examples[0].source ==
                'import numpy as np\na = np.array([1, 2, 3, 4]) / 3'
        )
        assert tests[0].examples[1].source == 'print(a)'
