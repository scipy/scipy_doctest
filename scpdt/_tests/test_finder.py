from . import finder_cases
from .._util import get_all_list

def test_get_all_list():
    items, depr, other = get_all_list(finder_cases)
    assert sorted(items) == ['Klass', 'func']

    # remove __all__, repeat
    del finder_cases.__all__
    items, depr, other = get_all_list(finder_cases)
    assert sorted(items) == ['Klass', 'func', 'private_func']

