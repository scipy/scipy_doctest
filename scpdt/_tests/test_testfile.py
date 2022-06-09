from .._frontend import testfile as doctestfile
from .._impl import DTConfig

def test_one_scipy_tutorial():
    # FIXME: HACK, will not work if scipy is not installed, 
    path = '/home/br/repos/scipy/scipy/doc/source/tutorial/ndimage.rst'

    config = DTConfig()
    config.stopwords = {}

    doctestfile(path, module_relative=False, verbose=2, raise_on_error=False, config=config)

