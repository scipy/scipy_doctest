"""
A pytest plugin that provides enhanced doctesting for Pydata libraries
"""

# import doctest
from _pytest import doctest

from scpdt.impl import DTChecker, DTConfig

def pytest_addoption(parser):
    """
    Register argparse-style options and ini-style config values,
    called once at the beginning of a test run.
    """
    parser.addoption(
        "--doctest-scpt", 
        action="store_true",
        help="Enable doctesting for pydata libraries."
        )

def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """
    if config.pluginmanager.getplugin('doctest'):
        config.pluginmanager.register(DTChecker())

    use_scpdt = config.getoption("doctest_scpdt")
    if not use_scpdt:
        return

    doctest._get_checker = _get_checker

def _get_checker():
    """
    Override function to return the DTChecker
    """
    return DTChecker()
