# Changelog

## 2.0 (2025-08-05)

- The default for the CLI option `--doctest-only-doctests` is changed to `False`.
  **This is a breaking change.** From now on, the default behavior of
  `$ pytest --doctest-modules` is to collect both doctests and unit tests, which aligns
  with the rest of the ecosystem. To retain the previous behavior of only collecting
  doctests, use `$ pytest --doctest-modules --doctest-only-doctests=true` explicitly.
  See [gh-198](https://github.com/scipy/scipy_doctest/issues/198) for details.

- A new `pytest_extra_requires` key was added to `DTConfig`. This allows to express
  dependencies of individual functions or modules, and only collect doctests if
  the specified requirements are met. As a made-up example,

```
config = DTConfig()
config.pytest_extra_requires ={"full.func.name" : ["cupy", "numpy>2"]}
```

will only collect doctests from the docstring of `full.func.name` if `cupy` is available,
and if `numpy` is at version `2.0` or above.
Parsing requirements relies on the [`packaging` module from PyPA](https://github.com/pypa/packaging).


## 1.8 (2025-05-29)

- Add a CLI option, `--doctest-only-doctests={true,false}` to control whether to only
  collect doctests (`true`, default) or also collect "regular" unit tests (`false`).
  Currently the default is to only collect doctests; in a next major version, the
  default will change to `false` to align the behavior of `pytest --doctest-modules`
  with the vanilla pytest behavior. See [gh-198](https://github.com/scipy/scipy_doctest/issues/198)
  for discussion.
- Fix doctesting dictionaries. Previously, only keys were checked and the values
  were not.
- Work around [a pytest issue](https://github.com/pytest-dev/pytest/discussions/13353),
  which led to spurious test failures with `scipy>=1.5`.
  See [gh-184](https://github.com/scipy/scipy_doctest/issues/184) for details.


## v1.7.1 (2025-04-04)

This version fixes a packaging error of v1.7, where the wheel and sdist contained extra files and
is identical to v1.7 otherwise.

## v1.7 (2025-04-04)

- Support python 3.13. The patch by Ben Beasley.
  Starting from python 3.13, the standard library `doctest.DoctestRunner` tracks the
  number of skipped doctests, in addition to the counts of attempted and failed
  doctests. We track this change, thus both the return value of `DTRunner.run` and
  `DTRunner.get_history` contain this count on python 3.13+ and do not contain it on
  prior python versions.


## v1.6 (2024-12-17)

- Fix a collection issue, where the DocTestFinder was missing docstrings of data
  descriptors. This is a workaround for an upstream issue,
  https://github.com/python/cpython/issues/127962. The patch by Matti Picus.
- Fix a collection issue, where the DocTestFinder was missing docstrings of public
  methods inherited from a private superclass. This was causing issues with some
  SciPy docstrings not being checked.


## v1.5.1 (2024-12-09)

- Improve handling of NumPy's abbreviation of large arrays: starting from version 2.2,
  NumPy displays the size of an array via a `shape=` argument:

```
>>> np.ones(10_000)
>>> array([1., 1., 1., ..., 1., 1., 1.], shape=(10000,))
```

  We now ignore the `shape=` part on NumPy < 2.2 and check the value on newer versions.


## v1.4 (2024-09-23)

- Add a `strict_check` configuration flag to decide whether to require matching dtypes
  or rely on NumPy's lax definition of equality: 

```
>>> np.float64(3) == 3
True
```

- Allow placing the `# may vary` modifier at either the source or the output of the doctest.
- Fix an issue with `local_resourses`, tests opening external files. The patch is from
  Sheila Kahwai.


## v1.3 (2024-06-22)

- Fix the interaction with pytest assertion rewriting.

## v1.2 (2024-06-08)

- More robust handling of printed numpy arrays in doctests.
- More robust checking of docstrings of deprecated functions.
- Fix an issue with handling lists/tuples: previously, the checker did not
  distinguish lists from tuples or other array-likes. The patch is from Luiz Eduardo Amaral.
- Fix an issue with the checker missing items for lists/tuples of mismatched lengths
  The patch is from Luiz Eduardo Amaral.


## v1.1 (2024-05-15)

Implementation the pytest plugin layer. The bulk of work done by Sheila Kahwai.
The preferred way to run the doctesting is now via pytest.


## v1.0 (2023-07-13)

This is the first release of a standalone package, following the extraction of the
core functionality from SciPy's and NumPy's `refguide-check` utilities.
