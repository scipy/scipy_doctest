import os
import sys
import importlib

from scpdt import testmod
from scpdt._util import get_all_list


BASE_MODULE = "scipy"

PUBLIC_SUBMODULES = [
    'cluster',
    'cluster.hierarchy',
    'cluster.vq',
    'constants',     ## obj.__name__
    'fft',
    'fftpack',
    'fftpack.convolve',
    'integrate',
    'interpolate',
    'io',
    'io.arff',
    'io.matlab',
    'io.wavfile',
    'linalg',
    'linalg.blas',
    'linalg.lapack',
    'linalg.interpolative',
    'misc',
    'ndimage',
    'odr',
    'optimize',
    'signal',
    'signal.windows',
    'sparse',
    'sparse.csgraph',
    'sparse.linalg',
    'spatial',
    'spatial.distance',
    'spatial.transform',
    'special',
    'stats',
    'stats.mstats',
    'stats.contingency',
    'stats.qmc',
    'stats.sampling'
]

# Docs for these modules are included in the parent module
OTHER_MODULE_DOCS = {
    'fftpack.convolve': 'fftpack',
    'io.wavfile': 'io',
    'io.arff': 'io',
}

# these names are known to fail doctesting and we like to keep it that way
# e.g. sometimes pseudocode is acceptable etc
DOCTEST_SKIPLIST = set([
    'scipy.stats.kstwobign',  # inaccurate cdf or ppf
    'scipy.stats.levy_stable',
    'scipy.special.sinc',  # comes from numpy
    'scipy.misc.who',  # comes from numpy
    'scipy.optimize.show_options',
    'io.rst',   # XXX: need to figure out how to deal w/ mat files
])


#### FIXME ####

os.environ['SCIPY_PIL_IMAGE_VIEWER'] = 'true'


#module_names = ['fft', 'linalg']
module_names = PUBLIC_SUBMODULES

dots = True
all_success = True
results = []


for submodule_name in module_names:
    prefix = BASE_MODULE + '.'
    if not submodule_name.startswith(prefix):
        module_name = prefix + submodule_name
    else:
        module_name = submodule_name

    module = importlib.import_module(module_name)

    full_name = module.__name__
    sys.stderr.write("\n\n" + "="*len(full_name) + "\n" + full_name + "\n" + "="*len(full_name) + "\n")

    result, history = testmod(module, strategy='public') 

    sys.stderr.write(str(result))

    all_success = all_success and (result.failed == 0)


# final report
if all_success:
    sys.stderr.write('\n>>>> OK: doctests PASSED\n')
    sys.exit(0)
else:
    sys.stderr.write('\n>>>> ERROR: doctests have errors\n')
    sys.exit(-1)




'''

    for module, mod_results in results:
        success = all(x[1] for x in mod_results)
        all_success = all_success and success

        if success and args.verbose == 0:
            continue

        print("")
        print("=" * len(module.__name__))
        print(module.__name__)
        print("=" * len(module.__name__))
        print("")

        for name, success, output in mod_results:
            if name is None:
                if not success or args.verbose >= 1:
                    print(output.strip())
                    print("")
            elif not success or (args.verbose >= 2 and output.strip()):
                print(name)
                print("-"*len(name))
                print("")
                print(output.strip())
                print("")

    if all_success:
        print("\nOK: refguide and doctests checks passed!")
        sys.exit(0)
    else:
        print("\nERROR: refguide or doctests have errors")
        sys.exit(1)
'''
