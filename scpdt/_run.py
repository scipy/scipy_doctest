""" Copy-pasting my way through python/cpython/Lib/doctest.py. """

import sys
import os
import inspect
import doctest
from doctest import NORMALIZE_WHITESPACE, ELLIPSIS, IGNORE_EXCEPTION_DETAIL

from ._checker import DTChecker, DEFAULT_NAMESPACE, DTFinder, DTRunner, DebugDTRunner
from ._util import matplotlib_make_nongui as mpl, temp_cwd, get_public_objects


def find_doctests(module, strategy=None,
                  name=None, exclude_empty=False, globs=None, extraglobs=None,
                  use_dtfinder=True):
    """Find doctests in a module.

    Parameters
    ----------
    m : module
        The base module to look into
    stratety : str or list of objects, optional
        The strategy to use to find doctests.
        If "public", look into public, non-deprecated objects in the module.
        If a list of objects, only look into the docstring of these objects
        If None, use the standard `doctest` behavior.
        Default is None.

    """
    if use_dtfinder:
        finder = DTFinder(exclude_empty=exclude_empty)
    else:
        finder = doctest.DocTestFinder(exclude_empty=exclude_empty)

    if strategy is None:
        tests = finder.find(module, name, globs=globs, extraglobs=extraglobs)
        return tests

    if strategy == "public":
        items, failures = get_public_objects(module)
        # XXX: handle failures
    else:
        # strategy must then be a list of objects to look at
        if not isinstance(strategy, list):
            raise ValueError(f"Expected a list of objects, got {strategy}.")
        items = strategy[:]

    tests = []
    for item in items:
        if inspect.ismodule(item):
            # do not recurse, only inspect the module docstring
            _finder = DTFinder(recurse=False)
            t = _finder.find(item, globs=globs, extraglobs=extraglobs)
        else:
            t = finder.find(item, globs=globs, extraglobs=extraglobs)  # FIXME: name
        tests += t
    
    return tests


def testmod(m=None, name=None, globs=None, verbose=None,
            report=True, optionflags=0, extraglobs=None,
            raise_on_error=False, exclude_empty=True,
            use_dtfinder=True, strategy=None):
    """This is a `testmod` driver from the standard library, with minimal patches.

    1. hardcode optionflags
    2. use _checker.DTChecker
    3. an option to use the modified DTFinder
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
    if globs is None:
        globs = dict(DEFAULT_NAMESPACE)  # NB: copy

    # Find, parse, and run all tests in the given module.
    tests = find_doctests(m, strategy, name, exclude_empty, globs, extraglobs, use_dtfinder)

    flags = NORMALIZE_WHITESPACE | ELLIPSIS | IGNORE_EXCEPTION_DETAIL
    if raise_on_error:
        runner = DebugDTRunner(verbose=verbose, optionflags=flags)
    else:
        # our modifications
        runner = DTRunner(verbose=verbose, optionflags=flags)

    # our modifications
    with mpl(), temp_cwd():
        for test in tests:
  # XXX          print(test.name)
            runner.run(test)

    if report:
        runner.summarize()

    return doctest.TestResults(runner.failures, runner.tries)



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

    for filename in testfiles:
        if filename.endswith(".py"):
            # It is a module -- insert its dir into sys.path and try to
            # import it. If it is part of a package, that possibly
            # won't work because of package imports.
            dirname, filename = os.path.split(filename)
            sys.path.insert(0, dirname)
            m = __import__(filename[:-3])
            del sys.path[0]
            failures, _ = testmod(m, verbose=verbose, optionflags=options,
                                  use_dtfinder=use_dtfinder)
        else:
            failures, _ = testfile(filename, module_relative=False,
                                     verbose=verbose, optionflags=options)

        if failures:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(_test())
