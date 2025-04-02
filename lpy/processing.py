"""
Module contains functions for processing data filterring and smoothing

Author: Ammosov
"""

import numpy as np
import numpy.typing as npt
from scipy.signal import fftconvolve


def exp(x: npt.ArrayLike, k: float, c: float) -> npt.NDArray[np.float64]:
    """
    Exponent values.
    Parameters
    ----------
    x : array like
        Input values.
    k : float
        factor.
    c : float
        constant.

    Returns
    -------
    array like
        np.exp values.
    """
    return np.exp(k*x + c)


def smooth(x, avg, n=1):
    """
    Smoothes array values using scipy fftconvolve.
    Parameters
    ----------
    x : array like
        Input values.
    avg : int
        Defines window box size.
    n : int, optional
        Amount of iterations to apply smoothing. The default is 1.

    Returns
    -------
    array like
        Smoothed array.
    """
    if len(x) == 1:
        return x

    x_smooth = x
    for _ in range(n+1):
        box = np.ones(avg)/avg
        x_smooth = fftconvolve(x_smooth, box, mode='same')
    return x_smooth


def detect_peaks_iqr(data, q1=25, q3=75):
    """
    Detect outliers in data using the interquartile range (IQR) method.

    Parameters
    ----------
    data : array_like
        Input data array where peaks need to be detected.
    q1 : float, optional
        Lower percentile for IQR calculation (default: 25).
    q3 : float, optional
        Upper percentile for IQR calculation (default: 75).

    Returns
    -------
    ndarray
        Array of indices where outliers (peaks) are detected.

    Notes
    -----
    Outliers are defined as values outside of:
    [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    where Q1 and Q3 are the specified percentiles.
    """
    q1 = np.percentile(data, q1)
    q3 = np.percentile(data, q3)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    spike_indices = np.where((data < lower_bound) | (data > upper_bound))[0]
    return spike_indices


def remove_peaks_iqr(x, y, q1=25, q3=75, mode="mask"):
    """
   Remove or mask outliers in data using IQR method.

   Parameters
   ----------
   x : array_like
       Time or x-axis values.
   y : array_like
       Data values corresponding to x.
   q1 : float, optional
       Lower percentile for IQR calculation (default: 25).
   q3 : float, optional
       Upper percentile for IQR calculation (default: 75).
   mode : str, optional
       Processing mode:
       - "mask": remove outliers (default)
       - "zeros": set outliers to zeros

   Returns
   -------
   tuple
       (x, y) with outliers processed according to specified mode.

   See Also
   --------
   detect_peaks_IQR : Function used for peak detection.
   """
    peaks_idx = detect_peaks_iqr(y, q1=q1, q3=q3)
    if mode == "zeros":
        y[peaks_idx] = 0.0
    elif mode == "mask":
        mask = np.ones_like(y, dtype=bool)
        mask[peaks_idx] = False
        x = x[mask]
        y = y[mask]
    return x, y


def remove_nans(x, y, mode="mask"):
    """
    Handle NaN values in data.

    Parameters
    ----------
    x : array_like
        Time or x-axis values.
    y : array_like
        Data values corresponding to x.
    mode : str, optional
        Processing mode:
        - "mask": remove NaN values (default)
        - "zeros": set NaN values to zeros

    Returns
    -------
    tuple
        (x, y) with NaN values processed according to specified mode.
    """
    if mode == "zeros":
        y[np.isnan(y)] = 0.0
    elif mode == "mask":
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
    return x, y


def remove_negatives(x, y, mode="mask"):
    """
    Handle negative values in data.

    Parameters
    ----------
    x : array_like
        Time or x-axis values.
    y : array_like
        Data values corresponding to x.
    mode : str, optional
        Processing mode:
        - "mask": remove negative values (default)
        - "zeros": set negative values to zeros

    Returns
    -------
    tuple
        (x, y) with negative values processed according to specified mode.
    """
    if mode == "zeros":
        y[y <= 0] = 0.0
    elif mode == "mask":
        mask = y > 0
        x = x[mask]
        y = y[mask]
    return x, y


def remove_peaks_by_threshold(x, y, threshold, mode="mask"):
    """
    Removes peaks from y based on a specified threshold.

    Parameters:
    x (array-like): Time or index array corresponding to y.
    y (array-like): Data array from which peaks are to be removed.
    threshold (float): Threshold value to identify peaks.
    mode (str): Mode of operation, either "zeros" or "mask".

    Returns:
    tuple: Modified x and y arrays.
    """
    # Identify peaks based on the threshold
    peaks_idx = np.where(y > threshold)[0]

    if mode == "zeros":
        # Set peaks to zeros
        y[peaks_idx] = 0.0
    elif mode == "mask":
        # Create a mask to remove peaks
        mask = np.ones_like(y, dtype=bool)
        mask[peaks_idx] = False
        x = x[mask]
        y = y[mask]

    return x, y
