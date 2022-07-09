# Floating-point aware, human readable, numpy-compatible doctesting.

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

- *Doctesting is floating-point aware.* In a nutshell, the core check is
  `np.allclose(want, got, atol=..., rtol=...)`, with user-controllable abs
  and relative tolerances. In the example above (_sans_ `# doctest: +SKIP`),
  `want` is the desired output, `array([0.333, 0.669, 1])` and `got` is the
  actual output from numpy: `array([0.33333333, 0.66666667, 1.        ])`.

- *Human-readable skip markers.* Consider
  ```
  >>> np.random.randint(100)
  42     # may vary
  ```
Note that the markers (by default, `"# may vary"` and `"# random"`) are applied
to an example's output, not its source.

Also note a difference with respect to the standard `# doctest: +SKIP`: the latter
skips the example entirely, while these additional markers only skip checking
the output. Thus the example source needs to be valid python code still.

- A user-configurable list of *stopwords*. If an example contains a stopword,
  it is checked to be valid python, but the output is not checked. This can
  be useful e.g. for not littering the documentation with the output of
  `import matplotlib.pyplot as plt; plt.xlim([2.3, 4.5])`.

- A user-configurable list of *pseudocode* markers. If an example contains one
  of these markers, it is considered pseudocode and is not checked.
  This is useful for `from example import some_functions` and similar stanzas.

- *Doctest discovery* is somewhat more flexible then the standard library
  `doctest` module. Specifically, one can use `testmod(module, strategy='api')`
  to only examine public objects of a module. This is helpful for complex
  packages, with non-trivial internal file structure.

- *User configuration*. Essentially all aspects of the behavior are user
  configurable via a `DTConfig` instance attributes. See the `DTConfig`
  docstring for details.

## Install and test

```
$ pip install -e .
$ pytest --pyargs scpdt
```

## Usage

The API of the package closely follows that of the standard `doctest` module.
We strive to provide drop-in replacements, or nearly so.


### Basic usage

For example,

```
>>> from scipy import linalg
>>> from scpdt import testmod
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
$ python -m scpdt foo.py
```

Note that, just like `$ python -m doctest foo.py`, this may
fail if `foo.py` is a part of a package due to package imports.

Text files can also be CLI-checked:
```
$ python -m scpdt bar.rst
```


### More fine-grained control

More fine-grained control of the functionality is available via the following
classes

|   Class     |  `doctest` analog  |
|-------------|--------------------|
| `DTChecker` | `DocTestChecker`   |
| `DTParser`  | `DocTestParser`    |
| `DTRunner`  | `DocTestRunner`    |
| `DTFinder`  | `DocTestFinder`    |
| `DTContext` |       --           |

The `DTContext` class is just a bag class which holds various configuration
settings as attributes.  An instance of this class is passed around, so user
configuration is simply creating an instance, overriding an attribute and
passing the instance to `testmod` or constructors of `DT*` objects. Defaults
are provided, based on a long-term usage in SciPy.


## Prior art and related work

- `pytest` provides some limited floating-point aware `NumericLiteralChecker`.

- `pytest-doctestplus` plugin from the `AstroPy` project has similar goals.
  The package is well established and widely used. From a user perspective, main
  differences are: (i) `pytest-doctestplus` is more sensitive to formatting,
  including whitespace---this if numpy tweaks its output formatting, doctests
  may start failing; (ii) there is still a need for `# doctest: +FLOAT_CMP`
  directives; (iii) being a pytest plugin, `pytest-doctestplus` is tightly
  coupled to `pytest`. It thus needs to follow `pytest` releases, and
  some maintenance work may be required to adapt when `pytest` publishes a new
  release.

  This takes a different approach: we closely follow the `doctest` API and
  implementation, which are naturally way more stable then `pytest`. Cooking up
  a `pytest` plugin on top of this package is certainly doable and only needs a
  champion.

- `NumPy` and `SciPy` use modified doctesting in their `refguide-check` utilities.
  These utilities are tightly coupled to their libraries, and have been reported
  to be not easy to reason about, work with, and extend to other projects.

  This project is nothing but the core functionality of the modified
  `refguide-check` doctesting, extracted to a separate package. 
  We believe having it separate simplifies both addressing the needs of these
  two packages, and potential adoption by other projects.


### Bug reports, feature requests and contributions

This package is work in progress. Contributions are most welcome!
Please don't hesitate to open an issue in the tracker or send a pull request.

The current location of the issue tracker is https://github.com/ev-br/scpdt.
