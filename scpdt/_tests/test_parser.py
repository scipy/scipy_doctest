from .._impl import DTConfig, DTParser

def test_parser_default_config():
    # Test that parser adds the _ignore marker for stopwords
    config = DTConfig()
    parser = DTParser()

    string = "Text text \n >>> 1 + plt.xlim([1, 2])\n\n More text"
    examples = parser.get_examples(string, config=config)

    assert len(examples) == 1
    assert examples[0].source == "1 + plt.xlim([1, 2])\n"
    assert examples[0].want == "  # _ignore\n"


def test_parser_vanilla_config():
    # Test that no stopwords means no markers
    config = DTConfig()
    config.stopwords = set()
    parser = DTParser()

    string = "Text text \n >>> 1 + plt.xlim([1, 2])\n\n More text"
    examples = parser.get_examples(string, config=config)

    assert len(examples) == 1
    assert examples[0].source == "1 + plt.xlim([1, 2])\n"
    assert examples[0].want == ""
