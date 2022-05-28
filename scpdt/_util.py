"""
Assorted utilities.
"""
import warnings
from contextlib import contextmanager

@contextmanager
def matplotlib_make_headless():
    """ Temporarily make the matplotlib backend headless; close all figures on exit.
    """
    try:
        import matplotlib
        backend = matplotlib.get_backend()
        matplotlib.use('Agg')
    except ImportError:
        backend = None

    try:
        # Matplotlib issues UserWarnings on plt.show() with a headless backend,
        # Filter them out.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "Matplotlib", UserWarning)
            yield backend
    finally:
        if backend:
            import matplotlib.pyplot as plt
            plt.close('all')
            matplotlib.use(backend)

