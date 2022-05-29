from . import finder_cases
from .._util import get_all_list, get_public_objects

def test_get_all_list():
    items, depr, other = get_all_list(finder_cases)
    assert sorted(items) == ['Klass', 'func']


def test_get_all_list_no_all():
    # test get_all_list on a module which does not define all.
    # XXX: remove __all__, test, reload on exit. 
    try:
        del finder_cases.__all__
        items, depr, other = get_all_list(finder_cases)
        assert sorted(items) == ['Klass', 'func', 'private_func']
    finally:
        from importlib import reload
        reload(finder_cases)


def test_get_objects():
    items, failures = get_public_objects(finder_cases)
    assert items == [finder_cases.func, finder_cases.Klass]
    assert failures == []

