""" Copy-pasting my way through python/cpython/Lib/doctest.py. """

import sys
import os
import inspect
import operator
import contextlib
import doctest

from ._checker import DTChecker, DTFinder, DTRunner, DebugDTRunner, DTConfig
from ._util import matplotlib_make_nongui as mpl, temp_cwd, get_public_objects


def find_doctests(module, strategy=None,
                  # doctest parameters. These fall through to the DocTestFinder
                  name=None, exclude_empty=True, globs=None, extraglobs=None,
                  # our configuration
                  config=None):
    """Find doctests in a module.

    Parameters
    ----------
    m : module
        The base module to look into
    strategy : str or list of objects, optional
        The strategy to use to find doctests.
        If "public", look into public, non-deprecated objects in the module.
        If a list of objects, only look into the docstring of these objects
        If None, use the standard `doctest` behavior.
        Default is None.
    name : str, optional
        The name of the module. Is used to construct the names of DocTest
        objects. Default is the `module.__name__`.
    exclude_empty : bool, optional
        Comes from the stdlib `doctest` module. See Notes.
        Default is True.
    globs : dict, optional
        Comes from the stdlib `doctest` module. See Notes.
        Default is None.
    extraglobs : dict, optional
        Comes from the stdlib `doctest` module. See Notes.
        Default is None.
    config
        A `DTConfig` instance

    Returns
    -------
    tests : list
        A list of `doctest.DocTest`s that are defined by the module docstring,
        and by its contained objects’ docstrings. The selection is controlled
        by the `strategy` argument. 

    Notes
    -----
    See https://docs.python.org/3/library/doctest.html#doctestfinder-objects
    for details on the `doctest`-inherited parameters (`name`, `globs`,
    `extraglobs`). Note that these are provided mainly for compatibility with
    the stdlib `doctest` and can be left with default values unless you are
    doing something unusual.

    """
    if config is None:
        config = DTConfig()

    finder = DTFinder(exclude_empty=exclude_empty)

    if strategy is None:
        tests = finder.find(module, name, globs=globs, extraglobs=extraglobs,
                            config=config)
        return tests

    if strategy == "public":
        (items, names), failures = get_public_objects(module)
        # XXX: handle failures
    else:
        # strategy must then be a list of objects to look at
        if not isinstance(strategy, list):
            raise ValueError(f"Expected a list of objects, got {strategy}.")
        items = strategy[:]
        names = [item.__name__ for item in items]

    tests = []
    for item, name in zip(items, names):
        if inspect.ismodule(item):
            # do not recurse, only inspect the module docstring
            _finder = DTFinder(recurse=False)
            t = _finder.find(item, name, globs=globs, extraglobs=extraglobs,
                             config=config)
        else:
            t = finder.find(item, name, globs=globs, extraglobs=extraglobs,
                            config=config)
        tests += t

    return tests



def _map_verbosity(level):
    """A helper for validating the verbosity level."""
    if level is None:
        level = 0
    level = operator.index(level)
    if level not in [0, 1, 2]:
        raise ValueError("Unknown verbosity setting : level = %s " % level)
    dtverbose = True if level == 2 else False
    return level, dtverbose


def testmod(m=None, name=None, globs=None, verbose=None,
            report=True, optionflags=0, extraglobs=None,
            raise_on_error=False, exclude_empty=True,
            strategy=None, config=None):
    """This is a `testmod` driver from the standard library, with minimal patches.

    1. hardcode optionflags
    2. use _checker.DTChecker
    4. an option for discovery of only public objects

       m=None, name=None, globs=None, verbose=None, report=True,
       optionflags=0, extraglobs=None, raise_on_error=False,
       exclude_empty=False
    Test examples in docstrings in functions and classes reachable
    from module m (or the current module if m is not supplied), starting
    with m.__doc__.
    Also test examples reachable from dict m.__test__ if it exists and is
    not None.  m.__test__ maps names to functions, classes and strings;
    function and class docstrings are tested even if the name is private;
    strings are tested directly, as if they were docstrings.
    Return (#failures, #tests).
    See help(doctest) for an overview.
    Optional keyword arg "name" gives the name of the module; by default
    use m.__name__.
    Optional keyword arg "globs" gives a dict to be used as the globals
    when executing examples; by default, use m.__dict__.  A copy of this
    dict is actually used for each docstring, so that each docstring's
    examples start with a clean slate.
    Optional keyword arg "extraglobs" gives a dictionary that should be
    merged into the globals that are used to execute examples.  By
    default, no extra globals are used.  This is new in 2.4.
    Optional keyword arg "verbose" prints lots of stuff if true, prints
    only failures if false; by default, it's true iff "-v" is in sys.argv.
    Optional keyword arg "report" prints a summary at the end when true,
    else prints nothing at the end.  In verbose mode, the summary is
    detailed, else very brief (in fact, empty if all tests passed).
    Optional keyword arg "optionflags" or's together module constants,
    and defaults to 0.  This is new in 2.3.  Possible values (see the
    docs for details):
        DONT_ACCEPT_TRUE_FOR_1
        DONT_ACCEPT_BLANKLINE
        NORMALIZE_WHITESPACE
        ELLIPSIS
        SKIP
        IGNORE_EXCEPTION_DETAIL
        REPORT_UDIFF
        REPORT_CDIFF
        REPORT_NDIFF
        REPORT_ONLY_FIRST_FAILURE
    Optional keyword arg "raise_on_error" raises an exception on the
    first unexpected exception or failure. This allows failures to be
    post-mortem debugged.
    Advanced tomfoolery:  testmod runs methods of a local instance of
    class doctest.Tester, then merges the results into (or creates)
    global Tester instance doctest.master.  Methods of doctest.master
    can be called directly too, if you want to do something unusual.
    Passing report=0 to testmod is especially useful then, to delay
    displaying a summary.  Invoke doctest.master.summarize(verbose)
    when you're done fiddling.


    Parameters
    ----------
    verbose : int
        Control verbosity: 0 means only report failures, 1 emit object names,
        2 is the max verbosity from doctest. Default is 0.

    Returns
    -------
    a tuple of a DocTestResult, and a dict with details of which objects were examined


    """
    # If no module was given, then use __main__.
    if m is None:
        # DWA - m will still be None if this wasn't invoked from the command
        # line, in which case the following TypeError is about as good an error
        # as we should expect
        m = sys.modules.get('__main__')

    # Check that we were actually given a module.
    if not inspect.ismodule(m):
        raise TypeError("testmod: module required; %r" % (m,))

    # If no name was given, then use the module's name.
    if name is None:
        name = m.__name__

    # out modifications
    if config is None:
        config = DTConfig()

    if globs is None:
        globs = dict(config.default_namespace)

    verbose, dtverbose = _map_verbosity(verbose)
    output = sys.stderr

    # Find, parse, and run all tests in the given module.
    tests = find_doctests(m, strategy, name, exclude_empty, globs, extraglobs, config=config)

    flags = config.optionflags
    if raise_on_error:
        runner = DebugDTRunner(verbose=dtverbose, optionflags=flags, config=config)
    else:
        # our modifications
        runner = DTRunner(verbose=dtverbose, optionflags=flags, config=config)

    # our modifications
    with mpl(), temp_cwd():
        for test in tests:
            if verbose == 1:
                output.write(test.name + '\n')
            runner.run(test, out=output.write)

    if report:
        runner.summarize()

    return doctest.TestResults(runner.failures, runner.tries), runner.get_history()


### THIS BELOW IS NOT TESTED, LIKELY BROKEN

def _test():
    import argparse

    parser = argparse.ArgumentParser(description="doctest runner")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='print very verbose output for all tests')
    parser.add_argument('-o', '--option', action='append',
                        choices=doctest.OPTIONFLAGS_BY_NAME.keys(), default=[],
                        help=('specify a doctest option flag to apply'
                              ' to the test run; may be specified more'
                              ' than once to apply multiple options'))
    parser.add_argument('-x', '--fail-fast', action='store_true',
                        help=('stop running tests after first failure (this'
                              ' is a shorthand for -o FAIL_FAST, and is'
                              ' in addition to any other -o options)'))
    parser.add_argument('-f', '--finder', action='store_false',
                        help='use `doctest.DocTestFinder` if given, otherwise'
                             ' use DTFinder.')
    parser.add_argument('file', nargs='+',
                        help='file containing the tests to run')
    args = parser.parse_args()
    testfiles = args.file
    # Verbose used to be handled by the "inspect argv" magic in DocTestRunner,
    # but since we are using argparse we are passing it manually now.
    verbose = args.verbose
    options = 0
    for option in args.option:
        options |= doctest.OPTIONFLAGS_BY_NAME[option]
    if args.fail_fast:
        options |= FAIL_FAST

    use_dtfinder = False
    if args.finder:
        use_dtfinder = True
        # FIXME: use config.stopwords=[] instead

    for filename in testfiles:
        if filename.endswith(".py"):
            # It is a module -- insert its dir into sys.path and try to
            # import it. If it is part of a package, that possibly
            # won't work because of package imports.
            dirname, filename = os.path.split(filename)
            sys.path.insert(0, dirname)
            m = __import__(filename[:-3])
            del sys.path[0]
            failures, _ = testmod(m, verbose=verbose, optionflags=options)
        else:
            failures, _ = testfile(filename, module_relative=False,
                                     verbose=verbose, optionflags=options)

        if failures:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(_test())
