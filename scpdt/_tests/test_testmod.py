from . import module_cases as module, stopwords_cases as stopwords
from .._run import testmod

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

