"""
A pytest plugin that provides enhanced doctesting for Pydata libraries
"""

# import doctest
from _pytest import doctest

from scpdt.impl import DTChecker, DTConfig


def pytest_configure(config):
    """
    Allow plugins and conftest files to perform initial configuration.
    """
    if config.pluginmanager.getplugin('doctest'):
        config.pluginmanager.register(DTChecker())

    doctest._get_checker = _get_checker

def _get_checker():
    """
    Override function to return the DTChecker
    """
    return DTChecker(config=DTConfig())
