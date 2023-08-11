from scpdt.impl import DTConfig


dt_config = DTConfig()

# Specify local files required by doctests
dt_config.local_resources = {'scpdt.tests.local_file_cases.local_files':
                                  ['scpdt/tests/local_file.txt'],
                            'scpdt.tests.local_file_cases.sio':
                                  ['scpdt/tests/octave_a.mat']   
                                  }