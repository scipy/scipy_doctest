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

