from . import test_module, test_stopwords
from .._run import testmod

def test(verbose=True, use_dtfinder=True):
    res_1 = testmod(test_module, verbose=verbose)
    res_2 = testmod(test_module, verbose=verbose, use_dtfinder=False)
    res_3 = testmod(test_stopwords, verbose=verbose)

    success = (all(_.failed == 0 for _ in [res_1, res_2, res_3]) and
               all(_.attempted > 0 for _ in [res_1, res_2, res_3]))

    if not success:
        mesg = f"tests failed: {res_1}, {res_2}, {res_3}"
        raise RuntimeError(mesg)

    return True
