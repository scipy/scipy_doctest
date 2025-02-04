# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'scipy_doctest'
copyright = '2025, SciPy Contributors'
author = 'SciPy Contributors'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Set the default role so we can use `text` instead of ``text``
default_role = "literal"

extensions = [
    'sphinx.ext.autodoc'
]

templates_path = ['_templates']
exclude_patterns = []

# The suffix(es) of source filenames.
source_suffix = [".rst"]

# The main toctree document.
master_doc = 'index'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_logo = '_static/logo.svg'
html_favicon = '_static/favicon.ico'
html_theme_options = {
    "github_url": "https://github.com/scipy/scipy_doctest",
    "logo": {
        "text": "SciPy Doctest",
    }
}

autosummary_generate = True

