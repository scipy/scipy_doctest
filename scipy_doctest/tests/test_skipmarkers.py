import doctest

try:
    import matplotlib.pyplot as plt    # noqa
    HAVE_MATPLOTLIB = True
except Exception:
    HAVE_MATPLOTLIB = False

import pytest

from ..impl import DTConfig, DTParser, DebugDTRunner


class TestSyntaxErrors:
    """Syntax errors trigger a doctest failure *unless* marked.

    Either mark it with +SKIP or as pseudocode.
    """
    @pytest.mark.skipif(not HAVE_MATPLOTLIB, reason='need matplotlib')
    def test_invalid_python(self):
        # This string raises
        # TypeError("unsupported operand type(s) for +: 'int' and 'tuple'")
        string = ">>> import matplotlib.pyplot as plt; 1 + plt.xlim([1, 2])\n"

        config = DTConfig()
        parser = DTParser(config)

        test = parser.get_doctest(string,
                                   globs=config.default_namespace,
                                   name='none: plain',
                                   filename='none',
                                   lineno=0)
        runner = DebugDTRunner()

        with pytest.raises(doctest.UnexpectedException) as exc_info:
            runner.run(test)

        orig_error = exc_info.value.exc_info  # unwrap pytest -> doctest -> example
        kind, value, traceback = orig_error

        assert kind is TypeError
        assert "unsupported operand type(s)" in value.args[0]

    def test_invalid_python_plus_skip(self):
        # Adding a '# doctest: +SKIP' turns it into pseudocode:
        # example NOT CHECKED, at all
        string = ">>> import matplotlib.pyplot as plt; 1 + plt.xlim([1, 2])"
        string += "  # doctest: +SKIP"

        config = DTConfig()
        parser = DTParser(config)

        test = parser.get_doctest(string,
                                   globs=config.default_namespace,
                                   name='none : +SKIP',
                                   filename='none',
                                   lineno=0)
        runner = DebugDTRunner()
        runner.run(test)
        assert runner.get_history() == {'none : +SKIP': (0, 0)}

    def test_invalid_python_pseudocode(self):
        # Marking a test as pseudocode is equivalent to a +SKIP:
        # example NOT CHECKED, at all
        string = ">>> import matplotlib.pyplot as plt; 1 + plt.xlim([1, 2])"

        config = DTConfig(pseudocode=['plt.xlim'])
        parser = DTParser(config)

        test = parser.get_doctest(string,
                                   globs=config.default_namespace,
                                   name='none : pseudocode',
                                   filename='none',
                                   lineno=0)
        runner = DebugDTRunner()
        runner.run(test)
        assert runner.get_history() == {'none : pseudocode': (0, 0)}


class TestPseudocodeMarkers:
    """Marking an example as pseudocode is exactly equivalent to a +SKIP."""

    def test_pseudocode_markers(self):
        # The first string has a +SKIP, the second one doesn't
        string = ">>> oops #doctest: +SKIP\n>>> ouch\n"

        parser = doctest.DocTestParser()
        test = parser.get_doctest(string, globs={},
                                  name='none', filename='none', lineno=0)

        opts_when_skipped = {doctest.OPTIONFLAGS_BY_NAME['SKIP']: True}
        assert len(test.examples) == 2
        assert test.examples[0].options == opts_when_skipped
        assert test.examples[1].options == {}

        # Now mark the second example as pseudocode
        config = DTConfig(pseudocode=['ouch'])
        parser = DTParser(config=config)
        test = parser.get_doctest(string, globs={},
                                  name='none', filename='none', lineno=0)

        assert len(test.examples) == 2
        assert test.examples[0].options == opts_when_skipped
        assert test.examples[1].options == opts_when_skipped


class TestStopwords:
    """If an example contains a stopword, the example still needs to be a valid
    python code, but the output is not checked.
    """
    @pytest.mark.skipif(not HAVE_MATPLOTLIB, reason='need matplotlib')
    def test_bogus_output(self):
        # 'plt.xlim(' is a stopword by default in the DTParser. This is because
        # it returns a tuple, which we don't want to litter our docstrings with.
        string = ">>> import matplotlib.pyplot as plt; plt.xlim([1, 2])\n"
        string += "bogus, not what plt.xlim(..) returns\n"

        parser = DTParser()
        test = parser.get_doctest(string, globs={},
                                  name='stopwords_bogus_output',
                                  filename='none', lineno=0)
        assert "bogus" in test.examples[0].want

        runner = DebugDTRunner()
        runner.run(test)

        # one example tried, of which zero failed
        assert runner.get_history() == {'stopwords_bogus_output': (0, 1)}


class TestMayVary:
    """The '# may vary' markers are applied to the example output, not source.

    Otherwise they are equivalent to declaring an example to have a stopword:
    the source needs to be valid python code, but the output is not checked.
    """
    def test_may_vary(self):
        string = ">>> 1 + 2\n"
        string += "uhm, not sure  # may vary\n"

        parser = DTParser()
        test = parser.get_doctest(string, globs={},
                                  name='may_vary_markers',
                                  filename='none', lineno=0)
        assert "uhm" in test.examples[0].want

        runner = DebugDTRunner()
        runner.run(test)

        # one example tried, of which zero failed
        assert runner.get_history() == {'may_vary_markers': (0, 1)}

    def test_may_vary_source(self):
        # The marker needs to be added to the example output, not source.
        string = ">>> 1 + 2  # may vary\n"
        string += "uhm, can't say\n"

        parser = DTParser()
        test = parser.get_doctest(string, globs={},
                                  name='may_vary_source',
                                  filename='none', lineno=0)

        runner = DebugDTRunner()
        runner.run(test)

        # one example tried, of which zero failed
        assert runner.get_history() == {'may_vary_source': (0, 1)}

    def test_may_vary_syntax_error(self):
        # `# may vary` markers do not mask syntax errors, unlike `# doctest: +SKIP`
        string = ">>> 1 += 2    # may vary\n"
        string += "42\n"

        parser = DTParser()
        test = parser.get_doctest(string, globs={},
                                  name='may_vary_err',
                                  filename='none', lineno=0)

        runner = DebugDTRunner()
        with pytest.raises(Exception) as exc_info:
            runner.run(test)
        assert exc_info.type == doctest.UnexpectedException


string='''\

This is an example string with doctests and skipblocks. A block is a sequence
of examples (which start with a >>> marker) without an intervening text, like
below

>>> from some_module import some_function    # doctest: +SKIPBLOCK
>>> some_function(42)

Note how the block above will fail doctesting unless the second line is
skipped. A standard solution is to add a +SKIP marker to every line, but this
is ugly and we skip the whole block instead. 

Once the block is over, we get back to usual doctests, which are not skipped

>>> 1 + 2
3

'''

def test_SKIPBLOCK():
    parser = DTParser()
    test = parser.get_doctest(string,
                               globs={},
                               name='SKIPBLOCK test',
                               filename='none',
                               lineno=0)

    SKIP = doctest.OPTIONFLAGS_BY_NAME['SKIP']

    assert len(test.examples) == 3
    assert test.examples[0].options[SKIP] is True
    assert test.examples[1].options[SKIP] is True
    assert test.examples[2].options == {}    # not skipped

