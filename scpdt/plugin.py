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

from scpdt.impl import DTChecker, DTParser, DTFinder, DebugDTRunner
from scpdt.conftest import dt_config
from .util import np_errstate, matplotlib_make_nongui

copied_files = []

def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """

    doctest._get_runner = _get_runner
    doctest._get_checker = _get_checker
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
        if dt_config.local_resources:
            copy_local_files(dt_config.local_resources, os.getcwd())

        # The `_pytest.doctest` module uses the internal doctest parsing mechanism.
        # We plugin scpdt's `DTFinder` that uses the `DTParser` which parses the doctest examples 
        # from the python module or file and filters out stopwords and pseudocode.
        finder = DTFinder(config=dt_config)
        optionflags = doctest.get_optionflags(self)

        # We plugin `PytestDTRunner`
        runner = _get_runner(
            verbose=False,
            optionflags=optionflags,
            checker=_get_checker()
        )

        # the rest remains unchanged
        for test in finder.find(module, module.__name__):
            if test.examples:  # skip empty doctests
                yield doctest.DoctestItem.from_parent(
                    self, name=test.name, runner=runner, dtest=test
                )


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
        if dt_config.local_resources:
            copy_local_files(dt_config.local_resources, os.getcwd())

        # We plugin `PytestDTRunner`
        runner = _get_runner(
            verbose=False,
            optionflags=optionflags,
            checker=_get_checker()
        )

        # We plug in an instance of `DTParser` which parses the doctest examples from the text file and
        # filters out stopwords and pseudocode.
        parser = _get_parser()

        # the rest remains unchanged
        test = parser.get_doctest(text, globs, name, filename, 0)
        if test.examples:
            yield doctest.DoctestItem.from_parent(
                self, name=test.name, runner=runner, dtest=test
            )


def _get_parser():
    """
    Return instance of DTParser
    """
    return DTParser(config=dt_config)


def _get_runner(checker, verbose, optionflags):
    import doctest
    """
    Override function to return instance of PytestDTRunner
    """
    class PytestDTRunner(DebugDTRunner):
        def run(self, test, compileflags=None, out=None, clear_globs=False):
            """
            Run tests in context managers:
            np_errstate: restores the numpy errstate and printoptions when done
            user_context_manager: allows user to plug in their own context manager
            matplotlib_make_nongui: temporarily make the matplotlib backend non-GUI
            """
            with np_errstate():
                with self.config.user_context_mgr(test):
                    with matplotlib_make_nongui():
                        super().run(test, compileflags=compileflags, out=out, clear_globs=clear_globs)
  
        """
        Almost verbatim copy of `_pytest.doctest.PytestDoctestRunner`.
        """
        def report_failure(self, out, test, example, got):
            failure = doctest.DocTestFailure(test, example, got)
            if self.config.nameerror_after_exception:
                out.append(failure)
            else:
                raise failure

        def report_unexpected_exception(self, out, test, example, exc_info):
            if isinstance(exc_info[1], OutcomeException):
                raise exc_info[1]
            if isinstance(exc_info[1], bdb.BdbQuit):
                outcomes.exit("Quitting debugger")
            failure = doctest.UnexpectedException(test, example, exc_info)
            if self.config.nameerror_after_exception:
                out.append(failure)
            else:
                raise failure

    return PytestDTRunner(checker=checker, verbose=verbose, optionflags=optionflags, config=dt_config)