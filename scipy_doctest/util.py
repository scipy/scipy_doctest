"""
Assorted utilities.
"""
import os
import warnings
import operator
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
        import matplotlib.pyplot as plt
        backend = matplotlib.get_backend()
        plt.close('all')
        matplotlib.use('Agg')
    except ImportError:
        backend = None

    try:
        # Matplotlib issues UserWarnings on plt.show() with a non-GUI backend,
        # Filter them out.
        # UserWarning: FigureCanvasAgg is non-interactive, and thus cannot be shown
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "FigureCanvasAgg", UserWarning)  # MPL >= 3.8.x
            warnings.filterwarnings("ignore", "Matplotlib", UserWarning)     # MPL <= 3.7.x
            yield backend
    finally:
        if backend:
            import matplotlib.pyplot as plt
            plt.close('all')
            matplotlib.use(backend)


@contextmanager
def temp_cwd(test, local_resources=None):
    """Switch to a temp directory, clean up when done.

        Copy local files, if requested.

        Parameters
        ----------
        test : doctest.DocTest instance
            The current test instance
        local_resources : dict, optional
            If provided, maps the name of the test (`test.name` attribute) to
            a list of filenames to copy to the tempdir. File names are relative
            to the `test.filename`, which is, in most cases, the name of the
            file the doctest has been extracted from.
    """
    cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()

    if local_resources and test.name in local_resources:
        # local files requested; copy the files
        path, _ = os.path.split(test.filename)
        for fname in local_resources[test.name]:
            shutil.copy(os.path.join(path, fname), tmpdir)
    try:
        os.chdir(tmpdir)
        yield tmpdir
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmpdir)


# Options for the usr_context_mgr : do nothing (default), and control the random
# state, in two flavors.

@contextmanager
def scipy_rndm_state():
    """Restore the `np.random` state when done."""
    # FIXME: this matches the refguide-check behavior, but is a tad strange:
    # makes sure that the seed the old-fashioned np.random* methods is *NOT* reproducible
    # but the new-style `default_rng()` *IS*.
    # Should these two be either both repro or both not repro?
    from scipy._lib._util import _fixed_default_rng
    import numpy as np
    with _fixed_default_rng():
        np.random.seed(None)
        yield


@contextmanager
def numpy_rndm_state():
    """Restore the `np.random` state when done."""
    # Make sure that the seed the old-fashioned np.random* methods is *NOT* reproducible
    import numpy as np
    np.random.seed(None)
    yield


@contextmanager
def noop_context_mgr(test=None):
    """Do nothing.

    This is a stub context manager to serve as a default for
    ``DTConfig().user_context_mgr``, for users to override.
    """
    yield


@contextmanager
def np_errstate():
    """A context manager to restore the numpy errstate and printoptions when done."""
    import numpy as np
    with np.errstate():
        with np.printoptions():
            yield


@contextmanager
def warnings_errors(test=None):
    """Temporarily turn all warnings to errors."""
    with warnings.catch_warnings():
        warnings.simplefilter('error', Warning)
        yield


def _map_verbosity(level):
    """A helper for validating/constructing the verbosity level.

    Validate that $ 0 <= level <= 2 $ and map the boolean flag for the
    `doctest.DocTestFinder` et al:
    0, 1 -> False, 2 -> True
    See the `testmod` docstring for details.


    Parameters
    ----------
    level : int or None
        Allowed values are 0, 1 or 2. None mean 0.

    Returns
    -------
    level : int
    dtverbose : bool

    """
    if level is None:
        level = 0
    level = operator.index(level)
    if level not in [0, 1, 2]:
        raise ValueError("Unknown verbosity setting : level = %s " % level)
    dtverbose = True if level == 2 else False
    return level, dtverbose


### Object / Doctest selection helpers ###


def is_deprecated(f):
    """ Check if an item is deprecated.
    """
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("error")
        try:
            f(**{"not a kwarg": None})
        except DeprecationWarning:
            return True
        except Exception:
            pass
        return False


def get_all_list(module):
    """Return a copy of the __all__ list with irrelevant items removed.
    The __all__list explicitly specifies which objects should be considered public.
    - If strategy="api" and __all__ is missing, return an empty list.
    - Also return a list of deprecated items and "other" items, which failed
      to classify.
    """
    if hasattr(module, "__all__"):
        all_list = copy.deepcopy(module.__all__)
    else:
        all_list = []
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


# XXX: not used ATM
modules = []
def generate_log(module, test):
    """
    Generate a log of the doctested items.
    
    This function logs the items being doctested to a file named 'doctest.log'.
    
    Args:
        module (module): The module being doctested.
        test (str): The name of the doctest item.
    """
    with open('doctest.log', 'a') as LOGFILE:
        try:
            if module.__name__ not in modules:
                LOGFILE.write("\n" + module.__name__ + "\n")
                LOGFILE.write("="*len(module.__name__) + "\n")
                modules.append(module.__name__)
            LOGFILE.write(f"{test}\n")
        except AttributeError:
            LOGFILE.write(f"{test}\n")

