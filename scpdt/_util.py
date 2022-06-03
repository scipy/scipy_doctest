"""
Assorted utilities.
"""
import os
import warnings
import shutil
import copy
import tempfile
import inspect
from contextlib import contextmanager

from doctest import NORMALIZE_WHITESPACE, ELLIPSIS, IGNORE_EXCEPTION_DETAIL

import numpy as np


class DTConfig:
    """A bag class to collect various configuration bits. 

    If an attribute is None, helpful defaults are subsituted.

    Attributes
    ----------
    default_namespace : dict
        The namespace to run examples in
    check_namespace : dict
        The namespace to do checks in
    rndm_markers : set
        Additional directives which act like `# doctest: + SKIP`
    optionflags : int
        doctest optionflags
    stopwords : list
        If an example contains any of these stopwords, do not check the output
        (but do check that the source is valid python)

    """
    def __init__(self, *, default_namespace=None, check_namespace=None,
                          rndm_markers=None,
                          # DTRunner configuration
                          optionflags=None,
                          # DTFinder configuration
                          stopwords=None):

        ### DTChecker configuration ###

        # The namespace to run examples in
        if default_namespace is None:
            default_namespace = {'np': np}
        self.default_namespace = default_namespace

        # The namespace to do checks in
        if check_namespace is None:
            check_namespace = {
                  'np': np,
                  'assert_allclose': np.testing.assert_allclose,
                  'assert_equal': np.testing.assert_equal,
                  # recognize numpy repr's
                  'array': np.array,
                  'matrix': np.matrix,
                  'masked_array': np.ma.masked_array,
                  'int64': np.int64,
                  'uint64': np.uint64,
                  'int8': np.int8,
                  'int32': np.int32,
                  'float32': np.float32,
                  'float64': np.float64,
                  'dtype': np.dtype,
                  'nan': np.nan,
                  'NaN': np.nan,
                  'inf': np.inf,
                  'Inf': np.inf,}
            self.check_namespace = check_namespace

        # Additional directives which act like `# doctest: + SKIP`
        if rndm_markers is None:
            rndm_markers = {'# random', '# Random',
                            '#random', '#Random',
                            "# may vary"}
        self.rndm_markers = rndm_markers

        ### DTRunner configuration ###

        # doctest optionflags
        if optionflags is None:
            optionflags = NORMALIZE_WHITESPACE | ELLIPSIS | IGNORE_EXCEPTION_DETAIL
        self.optionflags = optionflags

        ### DTFinder configuration ###

        # ignore examples which contain any of these stopwords
        if stopwords is None:
            stopwords = {'plt.', '.hist', '.show', '.ylim', '.subplot(',
                 'set_title', 'imshow', 'plt.show', '.axis(', '.plot(',
                 '.bar(', '.title', '.ylabel', '.xlabel', 'set_ylim', 'set_xlim',
                 '# reformatted', '.set_xlabel(', '.set_ylabel(', '.set_zlabel(',
                 '.set(xlim=', '.set(ylim=', '.set(xlabel=', '.set(ylabel=', '.xlim('}
        self.stopwords = stopwords


@contextmanager
def matplotlib_make_nongui():
    """ Temporarily make the matplotlib backend non-GUI; close all figures on exit.
    """
    try:
        import matplotlib
        backend = matplotlib.get_backend()
        matplotlib.use('Agg')
    except ImportError:
        backend = None

    try:
        # Matplotlib issues UserWarnings on plt.show() with a non-GUI backend,
        # Filter them out.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "Matplotlib", UserWarning)
            yield backend
    finally:
        if backend:
            import matplotlib.pyplot as plt
            plt.close('all')
            matplotlib.use(backend)


@contextmanager
def temp_cwd():
    """Switch to a temp directory, clean up when done."""
    cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        os.chdir(tmpdir)
        yield tmpdir
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmpdir)


def is_deprecated(f):
    """ Check if an item is deprecated.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("error")
        try:
            f(**{"not a kwarg":None})
        except DeprecationWarning:
            return True
        except Exception:
            pass
        return False


### Object / Doctest selection helpers ###

def get_all_list(module):
    """Return a copy of the __all__ list with irrelevant items removed.

    - If __all__ is missing, process the output of `dir(module)`.
    - Also return a list of deprecated items and "other" items, which failed
      to classify.
    """
    if hasattr(module, "__all__"):
        all_list = copy.deepcopy(module.__all__)
    else:
        all_list = copy.deepcopy(dir(module))
        all_list = [name for name in all_list
                    if not name.startswith("_")]
    for name in ['absolute_import', 'division', 'print_function']:
        try:
            all_list.remove(name)
        except ValueError:
            pass

    # Modules are almost always private; real submodules need a separate
    # run of refguide_check.
    all_list = [name for name in all_list
                if not inspect.ismodule(getattr(module, name, None))]

    deprecated = []
    not_deprecated = []
    for name in all_list:
        f = getattr(module, name, None)
        if callable(f) and is_deprecated(f):
            deprecated.append(name)
        else:
            not_deprecated.append(name)

    others = set(dir(module)).difference(set(deprecated)).difference(set(not_deprecated))

    return not_deprecated, deprecated, others


def get_public_objects(module, skiplist=None):
    """Return a list of public objects in a module.

    Parameters
    ----------
    module :
        A module look for objects
    skiplist : list
        The list of names to skip

    Returns
    -------
    (items, names) : a tuple of two lists
        `items` is a list of public objects in the module
        `names` is a list of names of these objects. Each entry of this list
        is nothing but `item.__name__` *if the latter exists* :
        `name == item.__name__ if item.__name__`.
        Otherwise, the name is taken from the `__all__` list of the module.
    failures : list
        a list of names which failed to be found in the module

    """
    if skiplist is None:
        skiplist = set()

    all_list, _, _ = get_all_list(module)

    items, names, failures = [], [], []

    for name in all_list:
        full_name = module.__name__ + '.' + name

        if full_name in skiplist:
            continue

        try:
            obj = getattr(module, name)
            items.append(obj)
            names.append(name)
        except AttributeError:
            import traceback
            failures.append((full_name, False,
                            "Missing item!\n" +
                            traceback.format_exc()))
            continue

    return (items, names), failures

