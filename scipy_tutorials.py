import os
import glob

from scpdt import testfile

base_dir = "/home/br/repos/scipy/scipy/doc/source/tutorial/"
tut_path = os.path.join(base_dir, '*.rst')
print('\nChecking tutorial files at %s:' % os.path.relpath(tut_path, os.getcwd()))

for filename in sorted(glob.glob(tut_path)):
  #  print(filename)
  #  print("="*len(filename))

    testfile(filename, module_relative=False, verbose=1, raise_on_error=False, report=True)

