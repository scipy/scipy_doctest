from . import module_cases as module, stopwords_cases as stopwords, finder_cases
from .._run import testmod, find_doctests

_VERBOSE = True


def test():
    test_module()
    test_module_vanilla_dtfinder()
    test_stopwords()


def test_module():
    res = testmod(module, verbose=_VERBOSE)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_module(DTFinder) failed)")
    return res


def test_module_vanilla_dtfinder():
    res = testmod(module, verbose=_VERBOSE, use_dtfinder=False)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_module(vanilla DocTestFinder) failed)")
    return res


def test_stopwords():
    res = testmod(stopwords, verbose=_VERBOSE)
    if res.failed != 0 or res.attempted == 0:
        raise RuntimeError("Test_stopwords failed.")
    return res


def test_public_obj_discovery():
    res = testmod(module, verbose=_VERBOSE, strategy='public')
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

