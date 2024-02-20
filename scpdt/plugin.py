"""
A pytest plugin that provides enhanced doctesting for Pydata libraries
"""
import bdb
import os
import shutil
import warnings

from _pytest import doctest, outcomes
from _pytest.doctest import DoctestModule, DoctestTextfile
from _pytest.pathlib import import_path
from _pytest.outcomes import skip, OutcomeException

from scpdt.impl import DTChecker, DTParser, DebugDTRunner
from scpdt.conftest import dt_config
from .util import np_errstate, matplotlib_make_nongui, generate_log
from scpdt.frontend import find_doctests


copied_files = []


def pytest_configure(config):
    """
    Perform initial configuration for the pytest plugin.
    """

    # Create a dt config attribute within pytest's config object for easy access.
    config.dt_config = dt_config

    # Override doctest's objects with the plugin's alternative implementation.
    doctest.DoctestModule = DTModule
    doctest.DoctestTextfile = DTTextfile


def pytest_unconfigure(config):
    """
    Called before exiting the test process.
    """

    # Delete all locally copied files in the current working directory
    if copied_files:
        try:
            for filepath in copied_files:
                os.remove(filepath)
        except FileNotFoundError:
            pass


def pytest_ignore_collect(collection_path, config):
    """
    Determine whether to ignore the specified collection path.
    This function is used to exclude the 'tests' directory and test modules when
    the '--doctest-modules' option is used.
    """
    if config.getoption("--doctest-modules"):
        path_str = str(collection_path)
        if "tests" in path_str or "test_" in path_str:
            return True


def pytest_collection_modifyitems(config, items):
    """
    This hook is executed after test collection and allows you to modify the list of collected items.

    The function removes
        - duplicate Doctest items (e.g., scipy.stats.norm and scipy.stats.distributions.norm)
        - Doctest items from underscored or otherwise private modules (e.g., scipy.special._precompute)

    Note that this functions cooperates with and cleans up after `DTModule.collect`, which does the
    bulk of the collection work.
    """
    # XXX: The logic in this function can probably be folded into DTModule.collect.
    # I (E.B.) quickly tried it and it does not seem to just work. Apparently something
    # pytest-y runs in between DTModule.collect and this hook (should that something
    # be the proper home for all collection?)

    if config.getoption("--doctest-modules"):
        unique_items = []

        for item in items:
            assert isinstance(item.parent, DTModule)

            # objects are collected twice: from their public module + from the impl module
            # e.g. for `levy_stable` we have
            # (Pdb) p item.name, item.parent.name
            # ('scipy.stats.levy_stable', 'build-install/lib/python3.10/site-packages/scipy/stats/__init__.py')
            # ('scipy.stats.distributions.levy_stable', 'distributions.py')
            # so we filter out the second occurence
            #
            # There are two options:
            #  - either the impl module has a leading underscore, or
            #  - it needs to be explicitly listed in 'extra_skips' config key
            #
            # Note that the last part cannot be automated: scipy.cluster.vq is public, but
            # scipy.stats.distributions is not
            extra_skips = config.dt_config.pytest_extra_skips

            parent_full_name = item.parent.module.__name__
            is_public = "._" not in parent_full_name
            is_duplicate = parent_full_name in  extra_skips or item.name in extra_skips

            if is_public and not is_duplicate:
                unique_items.append(item)

        # Replace the original list of test items with the unique ones
        items[:] = unique_items
    

def copy_local_files(local_resources, destination_dir):
    """
    Copy necessary local files for doctests to the current working directory.
    
    This function copies files specified in the `local_resources` attribute of a DTConfig instance
    to the specified `destination_dir`.
    
    Args:
        local_resources (dict): A dictionary of resources to be copied.
        destination_dir (str): The destination directory where files will be copied.
    
    Returns:
        list: A list of paths to the copied files.
    """
    for value in local_resources.values():
        for filepath in value:
            basename = os.path.basename(filepath)
            dest_path = os.path.join(destination_dir, basename)

            if not os.path.exists(dest_path):
                shutil.copy(filepath, destination_dir)
                copied_files.append(dest_path)    
    return copied_files


class DTModule(DoctestModule):
    """
    This class extends the DoctestModule class provided by pytest.
    
    DTModule is responsible for overriding the behavior of the collect method.
    The collect method is called by pytest to collect and generate test items for doctests
    in the specified module or file.
    """
    def collect(self):
        # Part of this code is copy-pasted from the `_pytest.doctest` module(pytest 7.4.0):
        # https://github.com/pytest-dev/pytest/blob/448563caaac559b8a3195edc58e8806aca8d2c71/src/_pytest/doctest.py#L497
        if self.path.name == "setup.py":
            return
        if self.path.name == "conftest.py":
            module = self.config.pluginmanager._importconftest(
                self.path,
                self.config.getoption("importmode"),
                rootpath=self.config.rootpath
            )
        else:
            try:
                module = import_path(
                    self.path,
                    root=self.config.rootpath,
                    mode=self.config.getoption("importmode"),
                )
            except ImportError:
                if self.config.getvalue("doctest_ignore_import_errors"):
                    skip("unable to import module %r" % self.path)
                else:
                    raise

        # Copy local files specified by the `local_resources` attribute to the current working directory
        if self.config.dt_config.local_resources:
            copy_local_files(self.config.dt_config.local_resources, os.getcwd())

        optionflags = doctest.get_optionflags(self)

        # Plug in the custom runner: `PytestDTRunner` 
        runner = _get_runner(self.config,
            verbose=False,
            optionflags=optionflags,
            checker=DTChecker(config=self.config.dt_config)
        )

        try:
            # We utilize scpdt's `find_doctests` function to discover doctests in public, non-deprecated objects in the module
            # NB: additional postprocessing in pytest_collection_modifyitems
            for test in find_doctests(module, strategy="api", name=module.__name__, config=dt_config):
#                if test.examples: # skip empty doctests  # FIXME: put this back (simplifies comparing the logs)
                    yield doctest.DoctestItem.from_parent(
                        self, name=test.name, runner=runner, dtest=test
                    )
        except:
            pass
        

class DTTextfile(DoctestTextfile):
    """
    This class extends the DoctestTextfile class provided by pytest.
    
    DTTextfile is responsible for overriding the behavior of the collect method.
    The collect method is called by pytest to collect and generate test items for doctests
    in the specified text files.
    """
    def collect(self):
        # Part of this code is copy-pasted from `_pytest.doctest` module(pytest 7.4.0):
        # https://github.com/pytest-dev/pytest/blob/448563caaac559b8a3195edc58e8806aca8d2c71/src/_pytest/doctest.py#L417
        encoding = self.config.getini("doctest_encoding")
        text = self.path.read_text(encoding)
        filename = str(self.path)
        name = self.path.name
        globs = {"__name__": "__main__"}

        optionflags = doctest.get_optionflags(self)

        # Copy local files specified by the `local_resources` attribute to the current working directory
        if self.config.dt_config.local_resources:
            copy_local_files(self.config.dt_config.local_resources, os.getcwd())

        # Plug in the custom runner: `PytestDTRunner`
        runner = _get_runner(self.config,
            verbose=False,
            optionflags=optionflags,
            checker=DTChecker(config=self.config.dt_config)
        )

        # Plug in an instance of `DTParser` which parses the doctest examples from the text file and
        # filters out stopwords and pseudocode.
        parser = DTParser(config=self.config.dt_config)

        # This part of the code is unchanged
        test = parser.get_doctest(text, globs, name, filename, 0)
        if test.examples:
            yield doctest.DoctestItem.from_parent(
                self, name=test.name, runner=runner, dtest=test
            )


def _get_runner(config, checker, verbose, optionflags):
    """
    Override function to return an instance of PytestDTRunner.
    
    This function creates and returns an instance of PytestDTRunner, a custom runner class
    that extends the behavior of DebugDTRunner for running doctests in pytest.
    """
    import doctest

    class PytestDTRunner(DebugDTRunner):
        def run(self, test, compileflags=None, out=None, clear_globs=False):
            """
            Run tests in context managers.
            
            Restore the errstate/print state after each docstring.
            Also, make MPL backend non-GUI and close the figures.
            
            The order of context managers is actually relevant. Consider
            user_context_mgr that turns warnings into errors.
            
            Additionally, suppose that MPL deprecates something and plt.something
            starts issuing warnings. Now all of those become errors
            *unless* the `mpl()` context mgr has a chance to filter them out
            *before* they become errors in `config.user_context_mgr()`.
            """
            with np_errstate():
                with config.dt_config.user_context_mgr(test):
                    with matplotlib_make_nongui():
                        # XXX: might want to add the filter to `testmod`, too
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=DeprecationWarning)
                            super().run(test, compileflags=compileflags, out=out, clear_globs=clear_globs)

        """
        Almost verbatim copy of `_pytest.doctest.PytestDoctestRunner` except we utilize
        DTConfig's `nameerror_after_exception` attribute in place of doctest's `continue_on_failure`.
        """
        def report_failure(self, out, test, example, got):
            failure = doctest.DocTestFailure(test, example, got)
            if config.dt_config.nameerror_after_exception:
                out.append(failure)
            else:
                raise failure

        def report_unexpected_exception(self, out, test, example, exc_info):
            if isinstance(exc_info[1], OutcomeException):
                raise exc_info[1]
            if isinstance(exc_info[1], bdb.BdbQuit):
                outcomes.exit("Quitting debugger")
            failure = doctest.UnexpectedException(test, example, exc_info)
            if config.dt_config.nameerror_after_exception:
                out.append(failure)
            else:
                raise failure
            
    return PytestDTRunner(checker=checker, verbose=verbose, optionflags=optionflags, config=config.dt_config)
