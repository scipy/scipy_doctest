"""
A pytest plugin that provides enhanced doctesting for Pydata libraries
"""
import bdb
import os
import shutil

from _pytest import doctest, outcomes
from _pytest.doctest import DoctestModule, DoctestTextfile
from _pytest.pathlib import import_path
from _pytest.outcomes import skip, OutcomeException

from scpdt.impl import DTChecker, DTParser, DebugDTRunner
from scpdt.conftest import dt_config
from .util import np_errstate, matplotlib_make_nongui
from scpdt.frontend import find_doctests


copied_files = []


def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """
    config.dt_config = dt_config
    doctest.DoctestModule = DTModule
    doctest.DoctestTextfile = DTTextfile

def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """

    # Delete all local files copied to the current working directory
    if copied_files:
        try:
            for filepath in copied_files:
                os.remove(filepath)
        except FileNotFoundError:
            pass


def pytest_ignore_collect(collection_path, config):
    """
    Ignore the tests directory and test modules
    """
    if config.getoption("--doctest-modules"):
        path_str = str(collection_path)
        if "tests" in path_str or "test_" in path_str:
            return True
        
    
def pytest_collection_modifyitems(config, items):
    """
    Remove duplicate Doctest items.

    Doctest items are collected from all public modules, including the __all__ attribute in __init__.py.
    This may lead to Doctest items being collected and tested more than once.
    We therefore need to remove the duplicate items by creating a new list with only unique items.

    This hook is executed after test collection and allows you to modify the list of collected items.
    """

    if config.getoption("--doctest-modules"):
        seen_test_names = set()
        unique_items = []

        for item in items:
            # Extract the item name, e.g., 'gauss_spline'
            # Example item: <DoctestItem scipy.signal._bsplines.gauss_spline>
            item_name = str(item).split('.')[-1].strip('>')

            # In case the preceding string represents a function or a class,
            # We need to keep the object name as both items represent different functions
            # eg:   <DoctestItem scipy.signal._ltisys.bode>
            #       <DoctestItem scipy.signal._ltisys.lti.bode>
            obj_name = str(item).split('.')[-2]
            
            # Extract the module path and name from the item's dtest attribute
            # Example dtest: <DocTest scipy.signal.__init__.gauss_spline from /scipy/build-install/lib/python3.10/site-packages/scipy/signal/_bsplines.py:226 (5 examples)>
            dtest = item.dtest
            path = str(dtest).split(' ')[3].split(':')[0]
            dtest_module = os.path.basename(path)

            # Import the module to check if the object name is an attribute of the module
            try:
                module = import_path(
                    path,
                    root=config.rootpath,
                    mode=config.getoption("importmode"),
                )
            except ImportError:
                module = None

            # Combine object name (if it exists), item name, and module name to create a unique identifier
            if module is not None  and obj_name != '__init__' and hasattr(module, obj_name) and callable(getattr(module, obj_name)):
                unique_test_name = f"{dtest_module}.{obj_name}.{item_name}"
            else:
                unique_test_name = f"{dtest_module}.{item_name}"

            # Check if the test name is unique and add it to the unique_items list if it is
            if unique_test_name not in seen_test_names:
                seen_test_names.add(unique_test_name)
                unique_items.append(item)

        # Replace the original list of test items with the unique ones
        items[:] = unique_items


def _get_checker():
    """
    Override function to return an instance of DTChecker
    """
    return DTChecker(config=dt_config)


def copy_local_files(local_resources, destination_dir):
    """
    Copy necessary local files for doctests to the current working directory. 
    The files to be copied are defined by the `local_resources` attribute of a DTConfig instance.
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
    The purpose of DTModule is to override the behavior of the collect method, 
    which is called by pytest to collect and generate test items for doctests in the 
    specified module or file.
    """
    def collect(self):
        # This code is copy-pasted from the `_pytest.doctest` module(pytest 7.4.0):
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

        # if local files are specified by the `local_resources` attribute, copy them to the current working directory
        if self.config.dt_config.local_resources:
            copy_local_files(self.config.dt_config.local_resources, os.getcwd())

        # The `_pytest.doctest` module uses the internal doctest parsing mechanism.
        # We plugin scpdt's `DTFinder` that uses the `DTParser` which parses the doctest examples 
        # from the python module or file and filters out stopwords and pseudocode.
        finder = DTFinder(config=self.config.dt_config)
        optionflags = doctest.get_optionflags(self)

        # We plug in `PytestDTRunner`
        runner = _get_runner(self.config,
            verbose=False,
            optionflags=optionflags,
            checker=DTChecker(config=self.config.dt_config)
        )
    
        try:
            # discover doctests in public, non-deprecated objects in the module
            for test in find_doctests(module, strategy="api", name=module.__name__, config=dt_config):
                if test.examples: # skip empty doctests
                    yield doctest.DoctestItem.from_parent(
                        self, name=test.name, runner=runner, dtest=test
                    )
        except:
            pass
        

class DTTextfile(DoctestTextfile):
    """
    This class extends the DoctestTextfile class provided by pytest. 
    The purpose of DTTextfile is to override the behavior of the collect method, 
    which is called by pytest to collect and generate test items for doctests in 
    the specified text files.
    """
    def collect(self):
        # This code is copy-pasted from `_pytest.doctest` module(pytest 7.4.0):
        # https://github.com/pytest-dev/pytest/blob/448563caaac559b8a3195edc58e8806aca8d2c71/src/_pytest/doctest.py#L417
        encoding = self.config.getini("doctest_encoding")
        text = self.path.read_text(encoding)
        filename = str(self.path)
        name = self.path.name
        globs = {"__name__": "__main__"}

        optionflags = doctest.get_optionflags(self)

        # if local files are specified by the `local_resources` attribute, copy them to the current working directory
        if self.config.dt_config.local_resources:
            copy_local_files(self.config.dt_config.local_resources, os.getcwd())

        # We plug in `PytestDTRunner`
        runner = _get_runner(self.config,
            verbose=False,
            optionflags=optionflags,
            checker=DTChecker(config=self.config.dt_config)
        )

        # We plug in an instance of `DTParser` which parses the doctest examples from the text file and
        # filters out stopwords and pseudocode.
        parser = DTParser(config=self.config.dt_config)

        # the rest remains unchanged
        test = parser.get_doctest(text, globs, name, filename, 0)
        if test.examples:
            yield doctest.DoctestItem.from_parent(
                self, name=test.name, runner=runner, dtest=test
            )


def _get_runner(config, checker, verbose, optionflags):
    import doctest
    """
    Override function to return instance of PytestDTRunner
    """
    class PytestDTRunner(DebugDTRunner):
        def run(self, test, compileflags=None, out=None, clear_globs=False):
            """
            Run tests in context managers.
            Restore the errstate/print state after each docstring.
            Also make MPL backend non-GUI and close the figures.
            The order of context managers is actually relevant. Consider
            user_context_mgr that turns warnings into errors.
            Additionally, suppose that MPL deprecates something and plt.something
            starts issuing warngings. Now all of those become errors
            *unless* the `mpl()` context mgr has a chance to filter them out
            *before* they become errors in `config.user_context_mgr()`.
            """
            with np_errstate():
                with config.dt_config.user_context_mgr(test):
                    with matplotlib_make_nongui():
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


modules = []
def generate_log(module, test):
    with open('doctest.log', 'a') as LOGFILE:
        if module.__name__ not in modules:
            LOGFILE.write("\n" + module.__name__ + "\n")
            LOGFILE.write("="*len(module.__name__) + "\n")
            modules.append(module.__name__)
        LOGFILE.write(test.name + "\n")