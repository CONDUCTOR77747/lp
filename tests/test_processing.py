# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 17:53:05 2025

@author: Ammosov
"""

import pytest
import numpy as np
from lpy.processing import (smooth, detect_peaks_iqr, remove_peaks_iqr,
                            remove_nans, remove_negatives)

# %% test smooth function


def test_smooth_basic():
    """ Test smooth function base case """
    x = np.array([1, 2, 3, 4, 5])
    smoothed = smooth(x, avg=3, n=1)
    expected = np.array([1., 2., 3., 3.33333333, 2.33333333])
    assert np.allclose(smoothed, expected, rtol=1e-2)


def test_smooth_empty_array():
    """ Test smooth function empty array case """
    x = np.array([])
    smoothed = smooth(x, avg=3, n=1)
    # Exact equality for edge case
    assert np.array_equal(smoothed, np.array([]))


def test_smooth_single_element():
    """ Test smooth function single element case """
    x = np.array([1])
    smoothed = smooth(x, avg=3, n=1)
    # Exact equality for single element
    assert np.array_equal(smoothed, np.array([1]))


def test_smooth_multiple_iterations():
    """ Test smooth function single multiple iterations case """
    x = np.array([1, 2, 3, 4, 5])
    smoothed = smooth(x, avg=3, n=2)
    expected = np.array([1., 2., 2.77777778, 2.88888889, 1.88888889])
    assert np.allclose(smoothed, expected, rtol=1e-2)


def test_smooth_zeros():
    """ Test smooth function single zero array case """
    x = np.zeros(5)
    smoothed = smooth(x, avg=3, n=1)
    assert np.array_equal(smoothed, np.zeros(5))  # Exact equality for zeros

# %% test remove functions


def test_detect_peaks_iqr():
    """ Test detect_peaks_iqr function.
        Check if peak on index 3 - value 100.
    """
    data = np.array([1, 2, 3, 100, 2, 3, 1])
    peaks = detect_peaks_iqr(data, q1=25, q3=75)
    assert np.array_equal(peaks, np.array([3]))


def test_remove_peaks_iqr():
    """ Test remove_peaks_iqr function, should remove 100 value peak """
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, 2, 100, 2, 1])
    # case 1 mode == "mask"
    x_new, y_new = remove_peaks_iqr(x, y, mode="mask")
    assert np.array_equal(x_new, np.array([1, 2, 4, 5]))
    assert np.array_equal(y_new, np.array([1, 2, 2, 1]))
    #  case 2 mode == "zeros"
    x_new, y_new = remove_peaks_iqr(x, y, mode="zeros")
    assert np.array_equal(x_new, np.array([1, 2, 3, 4, 5]))
    assert np.array_equal(y_new, np.array([1, 2, 0, 2, 1]))


def test_remove_nans():
    """ Test remove_nans function, should remove nans """
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, np.nan, 3, np.nan, 5])
    # case 1 mode == "mask"
    x_new, y_new = remove_nans(x, y, mode="mask")
    assert np.array_equal(x_new, np.array([1, 3, 5]))
    assert np.array_equal(y_new, np.array([1, 3, 5]))
    #  case 2 mode == "zeros"
    x_new, y_new = remove_nans(x, y, mode="zeros")
    assert np.array_equal(x_new, np.array([1, 2, 3, 4, 5]))
    assert np.array_equal(y_new, np.array([1, 0, 3, 0, 5]))


def test_remove_negatives():
    """ Test remove_nans function, should remove negatives """
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, -2, 3, -4, 5])
    # case 1 mode == "mask"
    x_new, y_new = remove_negatives(x, y, mode="mask")
    assert np.array_equal(x_new, np.array([1, 3, 5]))
    assert np.array_equal(y_new, np.array([1, 3, 5]))
    #  case 2 mode == "zeros"
    x_new, y_new = remove_negatives(x, y, mode="zeros")
    assert np.array_equal(x_new, np.array([1, 2, 3, 4, 5]))
    assert np.array_equal(y_new, np.array([1, 0, 3, 0, 5]))


if __name__ == "__main__":
    pytest.main()
