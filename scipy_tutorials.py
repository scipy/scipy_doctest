import os
import glob

from scpdt import testfile, DTConfig

base_dir = "/home/br/repos/scipy/scipy/doc/source/tutorial/"
tut_path = os.path.join(base_dir, '*.rst')
print('\nChecking tutorial files at %s:' % os.path.relpath(tut_path, os.getcwd()))

tutorials = [f for f in sorted(glob.glob(tut_path))]

# XXX: remove
tutorials = [f for f in tutorials if 'io.rst' not in f]
#tutorials = [f for f in tutorials if 'integrate' in f]

### set up scipy-specific config
config = DTConfig(pseudocode=set(['integrate.nquad(func,']))


for filename in tutorials:
    print(filename)
    print("="*len(filename))

    testfile(filename, module_relative=False,
             verbose=0, raise_on_error=False, report=True, config=config)

