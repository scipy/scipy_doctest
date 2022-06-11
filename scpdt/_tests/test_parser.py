import doctest
import pytest

from .._impl import DTConfig, DTParser, DebugDTRunner


def test_parser_default_config():
    # Test that parser adds the _ignore marker for stopwords
    parser = DTParser()

    string = "Text text \n >>> 1 + plt.xlim([1, 2])\n\n More text"
    examples = parser.get_examples(string)

    assert len(examples) == 1
    assert examples[0].source == "1 + plt.xlim([1, 2])\n"
    assert examples[0].want == "  # _ignore\n"


def test_parser_vanilla_config():
    # Test that no stopwords means no markers
    config = DTConfig()
    config.stopwords = set()
    parser = DTParser(config)

    string = "Text text \n >>> 1 + plt.xlim([1, 2])\n\n More text"
    examples = parser.get_examples(string)

    assert len(examples) == 1
    assert examples[0].source == "1 + plt.xlim([1, 2])\n"
    assert examples[0].want == ""


def test_config_nocopy():
    config = DTConfig()
    parser = DTParser(config)
    assert parser.config is config


def test_stopwords_invalid_python():
    # check that with ignore markers examples are still checked to be valid
    # python. This string raises
    # TypeError("unsupported operand type(s) for +: 'int' and 'tuple'")

    string = ">>> import matplotlib.pyplot as plt; 1 + plt.xlim([1, 2])\n"

    config = DTConfig()
    parser = DTParser(config)

    test = parser.get_doctest(string,
                               globs=config.default_namespace,
                               name='none',
                               filename='none',
                               lineno=0)
    runner = DebugDTRunner()
    with pytest.raises(doctest.UnexpectedException) as exc_info:
        runner.run(test)

    orig_error = exc_info.value.exc_info  # unwrap pytest -> doctest -> example
    kind, value, traceback = orig_error

    assert kind is TypeError
    assert "unsupported operand type(s)" in value.args[0]


def test_pseudocode_markers():
    # The first string has a +SKIP, the second one doesn't
    string = ">>> oops #doctest: +SKIP\n>>> ouch\n"

    parser = doctest.DocTestParser()
    test = parser.get_doctest(string, globs={},
                              name='none', filename='none', lineno=0)
    assert len(test.examples) == 2

    opts_when_skipped = {doctest.OPTIONFLAGS_BY_NAME['SKIP']: True}
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

