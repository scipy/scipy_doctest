"""Tests for N-dimensional array handling in DTChecker.

Regression tests for https://github.com/scipy/scipy_doctest/issues/21
"""

import doctest

import numpy as np

from ..impl import DTChecker, try_convert_printed_array


def test_try_convert_printed_array_1d():
    s = "[0 1 2]"
    out = try_convert_printed_array(s)
    assert eval(out) == [0, 1, 2]


def test_try_convert_printed_array_2d():
    s = "[[0 1 2]\n [3 4 5]]"
    out = try_convert_printed_array(s)
    assert eval(out) == [[0, 1, 2], [3, 4, 5]]


def test_try_convert_printed_array_3d():
    a = np.arange(24).reshape(2, 3, 4)
    out = try_convert_printed_array(str(a))
    assert np.array_equal(np.array(eval(out)), a)


def test_try_convert_printed_array_4d():
    a = np.arange(16).reshape(2, 2, 2, 2)
    out = try_convert_printed_array(str(a))
    assert np.array_equal(np.array(eval(out)), a)


def test_try_convert_printed_array_3d_floats():
    a = np.linspace(0.0, 1.0, 12).reshape(2, 2, 3)
    out = try_convert_printed_array(str(a))
    assert np.allclose(np.array(eval(out)), a)


def test_try_convert_printed_array_negatives():
    a = np.array([[[-1, 2], [3, -4]], [[5, -6], [-7, 8]]])
    out = try_convert_printed_array(str(a))
    assert np.array_equal(np.array(eval(out)), a)


def test_check_output_3d_printed_array():
    """A printed 3D array repr (no commas, blank line between slabs)
    should round-trip through the checker."""
    checker = DTChecker()
    a = np.arange(24).reshape(2, 3, 4)
    s = str(a)
    assert checker.check_output(s, s, doctest.ELLIPSIS)


def test_check_output_3d_array_repr_blankline():
    """The numpy `array(...)` repr with <BLANKLINE> directives passes."""
    checker = DTChecker()
    want = (
        "array([[[ 0,  1,  2,  3],\n"
        "        [ 4,  5,  6,  7],\n"
        "        [ 8,  9, 10, 11]],\n"
        "<BLANKLINE>\n"
        "       [[12, 13, 14, 15],\n"
        "        [16, 17, 18, 19],\n"
        "        [20, 21, 22, 23]]])"
    )
    got = repr(np.arange(24).reshape(2, 3, 4))
    assert checker.check_output(want, got, doctest.ELLIPSIS)


def test_check_output_3d_printed_with_tolerance():
    """Printed 3D arrays with floats slightly off should pass via np.allclose."""
    checker = DTChecker()
    a = np.linspace(0.0, 1.0, 12).reshape(2, 2, 3)
    want = str(a)
    b = a + 1e-9
    got = str(b)
    assert checker.check_output(want, got, doctest.ELLIPSIS)


def test_check_output_4d_printed_array():
    checker = DTChecker()
    a = np.arange(16).reshape(2, 2, 2, 2)
    s = str(a)
    assert checker.check_output(s, s, doctest.ELLIPSIS)
