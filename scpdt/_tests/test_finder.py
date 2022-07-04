import pytest

from . import finder_cases
from .._util import get_all_list, get_public_objects
from .._impl import DTFinder, DTConfig
from .._frontend import find_doctests

def test_get_all_list():
    items, depr, other = get_all_list(finder_cases)
    assert sorted(items) == ['Klass', 'func']


def test_get_all_list_no_all():
    # test get_all_list on a module which does not define all.
    # Remove __all__, test, reload on exit to not depend on the test order.
    try:
        del finder_cases.__all__
        items, depr, other = get_all_list(finder_cases)
        assert sorted(items) == ['Klass', 'func', 'private_func']
    finally:
        from importlib import reload
        reload(finder_cases)


def test_get_objects():
    (items, names), failures = get_public_objects(finder_cases)
    assert items == [finder_cases.func, finder_cases.Klass]
    assert names == [obj.__name__ for obj in items]
    assert failures == []


def test_get_objects_extra_items():
    # test get_all_list on a module which defines an incorrect all.
    # Patch __all__, test, reload on exit to not depend on the test order.
    try:
        finder_cases.__all__ += ['spurious']
        (items, names), failures = get_public_objects(finder_cases)

        assert items == [finder_cases.func, finder_cases.Klass]
        assert len(failures) == 1

        failed = failures[0]
        assert failed[0].endswith(".spurious")
        assert failed[2].startswith("Missing item")

    finally:
        from importlib import reload
        reload(finder_cases)


def test_find_doctests_extra_items():
    # test find_doctests on a module which defines an incorrect all.
    # Patch __all__, test, reload on exit to not depend on the test order.
    try:
        finder_cases.__all__ += ['spurious', 'missing']
        with pytest.raises(ValueError):
            find_doctests(finder_cases, strategy='api')
    finally:
        from importlib import reload
        reload(finder_cases)



def test_get_objects_skiplist():
    skips = [finder_cases.__name__ + '.' + 'func']
    (items, name), failures = get_public_objects(finder_cases, skiplist=skips)

    assert items == [finder_cases.Klass]
    assert failures == []


def test_dtfinder_config():
    config = DTConfig()
    finder = DTFinder(config=config)
    assert finder.config is config
