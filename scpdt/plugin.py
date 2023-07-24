"""
A pytest plugin that provides enhanced doctesting for Pydata libraries
"""

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
    Override function to return an instance of DTChecker with default configurations
    """
    return DTChecker(config=DTConfig())
