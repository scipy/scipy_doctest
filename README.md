# Floating-point aware, human readable, numpy-compatible doctesting.

[![PyPI version][pypi-version]][pypi-link]
[![Conda-Forge][conda-badge]][conda-link]

<!-- prettier-ignore-start -->
[conda-badge]:              https://img.shields.io/conda/vn/conda-forge/scipy-doctest
[conda-link]:               https://anaconda.org/conda-forge/scipy-doctest
[pypi-link]:                https://pypi.org/project/scipy-doctest/
[pypi-version]:             https://img.shields.io/pypi/v/scipy-doctest
<!-- prettier-ignore-end -->

## TL;DR

This project extends the standard library `doctest` module to allow flexibility
and easy customization of finding, parsing and checking code examples in
documentation.

Can be used either as drop-in `doctest` replacement or through the `pytest`
integration. Uses a floating-point aware doctest checker by default.

## Motivation and scope

Having examples in the documentation is great. Having wrong examples in the
documentation is not that great however.

The standard library `doctest` module is great for making sure that docstring
examples are correct. However, the `doctest` module is limited in several
respects. Consider:

```
 >>> np.array([1/3, 2/3, 3/3])   # doctest: +SKIP
 array([0.333, 0.669, 1])
```

This looks reasonably clear but does not work, in three different ways.
_First_, `1/3` is not equal to 0.333 because floating-point arithmetic.
_Second_, `numpy` adds whitespace to its output, this whitespace confuses the
`doctest`, which is whitespace-sensitive. Therefore, we added a magic directive,
`+SKIP` to avoid a doctest error. _Third_, the example is actually
wrong---notice `0.669` which is not equal to `2/3` to three sig figs. The error
went unnoticed by the doctester also because of the `+SKIP` directive.

We believe these `# doctest: +SKIP` directives do not add any value to
a human reader, and should not be present in the documentation.

This package defines modified doctesting routines which fix these deficiencies.
Its main features are

- _Doctesting is floating-point aware._ In a nutshell, the core check is
  `np.allclose(want, got, atol=..., rtol=...)`, with user-controllable abs
  and relative tolerances. In the example above (_sans_ `# doctest: +SKIP`),
  `want` is the desired output, `array([0.333, 0.669, 1])` and `got` is the
  actual output from numpy: `array([0.33333333, 0.66666667, 1.        ])`.

- _Human-readable skip markers._ Consider
  ```
  >>> np.random.randint(100)
  42     # may vary
  ```
  Note that the markers (by default, `"# may vary"` and `"# random"`) can be applied
  to either an example's output, or its source.

Also note a difference with respect to the standard `# doctest: +SKIP`: the latter
skips the example entirely, while these additional markers only skip checking
the output. Thus the example source needs to be valid python code still.

- A user-configurable list of _stopwords_. If an example contains a stopword,
  it is checked to be valid python, but the output is not checked. This can
  be useful e.g. for not littering the documentation with the output of
  `import matplotlib.pyplot as plt; plt.xlim([2.3, 4.5])`.

- A user-configurable list of _pseudocode_ markers. If an example contains one
  of these markers, it is considered pseudocode and is not checked.
  This is useful for `from example import some_functions` and similar stanzas.

- A `# doctest: +SKIPBLOCK` option flag to skip whole blocks of pseudocode. Here
  a 'block' is a sequence of doctest examples without any intervening text.

- _Doctest discovery_ is somewhat more flexible then the standard library
  `doctest` module. Specifically, one can use `testmod(module, strategy='api')`
  to only examine public objects of a module. This is helpful for complex
  packages, with non-trivial internal file structure. Alternatively, the default
  value of `strategy=None` is equivalent to the standard `doctest` module
  behavior.

- _User configuration_. Essentially all aspects of the behavior are user
  configurable via a `DTConfig` instance attributes. See the `DTConfig`
  docstring for details.

## Install and test

```
$ pip install scipy-doctest
$ pytest --pyargs scipy_doctest
```

## Usage

The API of the package has two layers: the basic layer follows the API of the
standard library `doctest` module, and we strive to provide drop-in replacements,
or nearly so.

The other layer is the `pytest` plugin.

### Run doctests via pytest

To run doctests on your package or project, follow these steps:

1. **Install the plugin**

```bash
pip install scipy-doctest
```

2. **Register or load the plugin**

Next, you need to register or load the pytest plugin within your test module or `conftest.py` file.

To do this, add the following line of code:

```python
# In your conftest.py file or test module

pytest_plugins = "scipy_doctest"
```

Check out the [pytest documentation](https://docs.pytest.org/en/stable/how-to/writing_plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file) for more information on requiring/loading plugins in a test module or `conftest.py` file.

3. **Run doctests**

Once the plugin is registered, run the doctests by executing the following command:

```bash
$ python -m pytest --doctest-modules
```

or

```bash
$ pytest --pyargs <your-package> --doctest-modules
```

By default, all doctests are collected. To only collect public objects, `strategy="api"`,
use the command flag

```bash
$ pytest --pyargs <your-package> --doctest-modules --doctest-collect=api
```

See [More fine-grained control](#more-fine-grained-control) section
for details on how to customize the behavior.

**NOTE** In versions 1.x, `pytest --doctest-modules` was only collecting doctests, and
skipped 'regular' unit tests. This differed from the vanilla `pytest` behavior, which
collects both doctests and unit tests.

The behavior was changed in version 2.0: from `scipy-doctest==2.0` the default is
changed to align with the vanilla `pytest`.

To retain the previous behavior and skip 'regular' unit tests, use the
`--doctest-only-doctests` CLI option:

```
$ pytest --doctest-modules --doctest-only-doctests=true
```


### Basic usage

The use of `pytest` is optional, and you can use the `doctest` layer API.
For example,

```
>>> from scipy import linalg
>>> from scipy_doctest import testmod
>>> res, hist = testmod(linalg, strategy='api')
>>> res
TestResults(failed=0, attempted=764)
```

The second return value, `hist` is a dict which maps the names of the objects
to the numbers of failures and attempts for individual examples.

For more details, see the `testmod` docstring. Other useful functions are
`find_doctests`, `run_docstring_examples` and `testfile` (the latter two mimic
the behavior of the eponymous functions of the `doctest` module).

### Command-line interface

There is a basic CLI, which also mimics that of the `doctest` module:

```
$ python -m scipy_doctest foo.py
```

Note that, just like `$ python -m doctest foo.py`, this may
fail if `foo.py` is a part of a package due to package imports.

Text files can also be CLI-checked:

```
$ python -m scipy_doctest bar.rst
```

Notice that the command-line usage only uses the default `DTConfig` settings.

(more-fine-grained-control)=

## More fine-grained control

More fine-grained control of the functionality is available via the following
classes

| Class       | `doctest` analog |
| ----------- | ---------------- |
| `DTChecker` | `DocTestChecker` |
| `DTParser`  | `DocTestParser`  |
| `DTRunner`  | `DocTestRunner`  |
| `DTFinder`  | `DocTestFinder`  |
| `DTContext` | --               |

The `DTContext` class is just a bag class which holds various configuration
settings as attributes. An instance of this class is passed around, so user
configuration is simply creating an instance, overriding an attribute and
passing the instance to `testmod` or constructors of `DT*` objects. Defaults
are provided, based on a long-term usage in SciPy.

See the [DTConfig docstring](https://github.com/scipy/scipy_doctest/blob/main/scipy_doctest/impl.py#L24)
for the full set of attributes that allow you to fine-tune your doctesting experience.

To set any of these attributes, create an instance of `DTConfig` and assign the attributes
in a usual way.

If using the pytest plugin, it is convenient to use the default instance, which
is predefined in `scipy_doctest/conftest.py`. This instance will be automatically
passed around via an
[attribute of pytest's `Config` object](https://github.com/scipy/scipy_doctest/blob/58ff06a837b7bff1dbac6560013fc6fd07952ae2/scipy_doctest/plugin.py#L39).

### Examples

```
dt_config = DTConfig()
```

or, if using pytest,

```python
from scipy_doctest.conftest import dt_config   # a DTConfig instance with default settings
```

and then

```
dt_config.rndm_markers = {'# unintialized'}

dt_config.stopwords = {'plt.', 'plt.hist', 'plt.show'}

dt_config.local_resources = {
    'scipy_doctest.tests.local_file_cases.local_files': ['scipy_doctest/tests/local_file.txt'],
    'scipy_doctest.tests.local_file_cases.sio': ['scipy_doctest/tests/octave_a.mat']
}

dt_config.skiplist = {
    'scipy.special.sinc',
    'scipy.misc.who',
    'scipy.optimize.show_options'
}
```

If you don't set these attributes, the [default settings](https://github.com/scipy/scipy_doctest/blob/58ff06a837b7bff1dbac6560013fc6fd07952ae2/scipy_doctest/impl.py#L94) of the attributes are used.

#### Alternative Checkers

By default, we use the floating-point aware `DTChecker`. If you want to use an
alternative checker, all you need to do is to define the corresponding class,
and add an attribute to the `DTConfig` instance. For example,

```
class VanillaOutputChecker(doctest.OutputChecker):
    """doctest.OutputChecker to drop in for DTChecker.

    LSP break: OutputChecker does not have __init__,
    here we add it to agree with DTChecker.
    """
    def __init__(self, config):
        pass
```

and

```
dt_config = DTConfig()
dt_config.CheckerKlass = VanillaOutputChecker
```

See [a pytest example](https://github.com/scipy/scipy_doctest/blob/main/scipy_doctest/tests/test_pytest_configuration.py#L63)
and [a doctest example](https://github.com/scipy/scipy_doctest/blob/main/scipy_doctest/tests/test_runner.py#L94)
for more details.

### NumPy and SciPy wrappers

NumPy wraps `scipy-doctest` with the `spin` command

```
$ spin check-docs
```

In SciPy, the name of the `spin` command is `smoke-docs`::

```
$ spin smoke-docs    # check docstrings
$ spin smoke-tutorials   # ReST user guide tutorials
```

## Rough edges and sharp bits

Here is a (non-exhaustive) list of possible gotchas:

#### _In-place development builds_.

Some tools (looking at you `meson-python`) simulate in-place builds with a
`build-install` directory. If this directory is located under the project root,
`pytest` is getting confused by duplicated items under the root and build-install
folders.

The solution is to make pytest only look into the `build-install` directory
(the specific path to `build-install` may vary):

```
$ pytest build-install/lib/python3.10/site-packages/scipy/ --doctest-modules
```

instead of `$ pytest --pyargs scipy`.

If you use actual editable installs, of the `pip install --no-build-isolation -e .` variety, you may
need to add `--import-mode=importlib` to the `pytest` invocation.

If push really comes to shove, you may try using the magic env variable:
` PY_IGNORE_IMPORTMISMATCH=1 pytest ...`,
however the need usually indicates an issue with the package itself.
(see [gh-107](https://github.com/scipy/scipy_doctest/pull/107) for an example).

#### _Optional dependencies are not that optional_

If your package contains optional dependencies, doctests do not know about them
being optional. So you either guard the imports in doctests themselves (yikes!), or
the collections fails if dependencies are not available.

The solution is to explicitly `--ignore` the paths to modules with optionals.
(or, equivalently, use `DTConfig.pytest_extra_ignore` list):

```
$ pytest --ignore=/build-install/lib/scipy/python3.10/site-packages/scipy/_lib ...
```

Note that installed packages are no different:

```
$ pytest --pyargs scipy --doctest-modules --ignore=/path/to/installed/scipy/_lib
```

#### _Doctest collection strategies_

The default collection strategy follows `doctest` module and `pytest`. This leads
to duplicates if your package has the split between public and \_private modules,
where public modules re-export things from private ones. The solution is to
use `$ pytest --doctest-collect=api` CLI switch: with this, only public
objects will be collected.

The decision on what is public is as follows: an object is public iff

  - it is included into the `__all__` list of a public module;
  - the name of the object does not have a leading underscore;
  - the name of the module from which the object is collected does not have
  a leading underscore.

Consider an example: `scipy.linalg.det` is defined in `scipy/linalg/_basic.py`,
so it is collected twice, from `_basic.py` and from `__init__.py`. The rule above
leads to

  - `scipy.linalg._basic.det`, collected from `scipy/linalg/_basic.py`, is private.
  - `scipy.linalg.det`, collected from `scipy/linalg/__init__.py`, is public.

#### _`pytest`'s assertion rewriting_

In some rare cases you may need to either explicitly register the `scipy_doctest`
package with the `pytest` assertion rewriting machinery, or ask it to avoid rewriting
completely, via `pytest --assert=plain`.
See [the `pytest documentation`](https://docs.pytest.org/en/7.1.x/how-to/assert.html)
for more details.

In general, rewriting assertions is not very useful for doctests, as the
output on error is fixed by the doctest machinery anyway. Therefore, we believe
adding `--assert=plain` is reasonable.

#### _Mixing strings and numbers_

Generally, we aim to handle mixtures of strings and numeric data. Deeply nested data
structures, however, may cause the checker to fall back to the vanilla `doctest` literal
checking. For instance, `["value", 1/3]` will use the floating-point aware checker, and
so will `{"value": 1/3, "other value": 2/3}` or `[(1, 2), (3, 4)]`; Meanwhile, nested
dictionaries, `{"a": dict(value=1/3)}`, or lists of tuples with mixed entries,
`[("a", 1/3), ("b", 2/3)]`, will currently fall back to vanilla `doctest` literal
comparisons.

We stress that no matter how tricky or deeply nested the output is, the worst case
scenario is that the floating-point aware checker is not used. If you have a case where
`doctest` works correctly and `scipy_doctest` does not, please report it as a bug.


## Prior art and related work

- `pytest` provides some limited floating-point aware `NumericLiteralChecker`.

- `pytest-doctestplus` plugin from the `AstroPy` project has similar goals.
  The package is well established and widely used. From a user perspective, main
  differences are: (i) `pytest-doctestplus` is more sensitive to formatting,
  including whitespace; (ii) there is still a need for `# doctest: +FLOAT_CMP`
  directives.

  This project takes a slightly different approach: we strive to make numeric comparisons
  whitespace insensitive and automatic, without a need for explicit markup.  For rare cases
  which require additional configuration, we either keep it in the tool (thus out of
  reader-visible docstrings), or provide human-readable markers (hence `# may vary`
  not `# doctest +SKIP`).
  Furthermore, in addition to plugging into `pytest`, we provide an API layer which closely
  follows the `doctest` API. Essentially all aspects of doctesting are user-configurable.

- `xdoctest` package relies on a deeper rewrite of the standard-library `doctest`
  functionality, and uses an AST-based analysis to parse code examples out of docstrings.

- `NumPy` and `SciPy` were using modified doctesting in their `refguide-check` utilities.
  These utilities were tightly coupled to their libraries, and have been reported
  to be not easy to reason about, work with, and extend to other projects.

  This project is mainly the core functionality of the modified `refguide-check` doctesting,
  extracted to a separate package. We believe having it separate simplifies both
  addressing the needs of these two packages, and adoption by other projects.


## Bug reports, feature requests and contributions

This package is work in progress. Contributions are most welcome!
Please don't hesitate to open an issue in the tracker or send a pull request.

The current location of the issue tracker is <https://github.com/scipy/scipy_doctest>.
