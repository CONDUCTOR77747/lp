# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 14:51:17 2025

@author: Ammosov

SpanDetector: Detects time spans for Te (electron temperature) and
ne (electron density) in Langmuir probe data.

The class identifies key features in probe voltage (u) and current (i) signals
to determine relevant time intervals for analysis.
"""

import numpy as np
from scipy.signal import argrelextrema
from ..processing import smooth


class SpanDetector():
    """
    Detects time spans for Te and ne analysis in Langmuir probe data.

    Parameters
    ----------
    t : ndarray
        1D array of time values in [ms].
    u : ndarray
        1D array of probe voltage in [V].
    i : ndarray
        1D array of probe current in [mA].

    Example:
        spandet = SpanDetector(t, u, i)
        spans_te = spandet.spans_te(dt_range, mode='up')
        spans_ne = spandet.spans_ne(dt_range)

    Attributes
    ----------
    u_smooth : ndarray
        Smoothed probe voltage.
    di : ndarray
        Smoothed gradient of probe current (scaled by 500).
    u_mins : ndarray
        indices of local minima in smoothed voltage (u_smooth).
    di_mins : ndarray
        indices of relevant local minima in di near u_mins.
    di_maxs : ndarray
        indices of relevant local maxima in di near u_mins.
    """

    def __init__(self, t, u, i):
        self.t, self.u, self.i = t, u, i
        self.calc_repere_points()

    def calc_repere_points(self):
        """Compute key reference points (minima/maxima) for span detection."""
        # smooth u, calc gradient of i (di), smooth di
        u_smooth = smooth(self.u, 151, 11)
        i_smooth = smooth(self.i, 71, 11)
        di = np.gradient(i_smooth)
        di = smooth(di, 71, 11)

        # save smoothed u and di
        self.u_smooth, self.di = u_smooth, di*500
        # calc minimums of u
        self.u_mins = argrelextrema(u_smooth, np.less)[0]
        # extract proper repere points of di
        self.di_mins = self.extract_di_mins(argrelextrema(di, np.less)[0])
        self.di_maxs = self.extract_di_maxs(argrelextrema(di, np.greater)[0])

    def extract_di_mins(self, di_mins_all):
        """Extract di minima nearest to each u minimum."""
        di_mins_ok = []
        for umin in self.u_mins:
            for i, imax in enumerate(di_mins_all):
                if imax > umin:
                    if i == 0:
                        continue
                    # first to the left from u_min
                    di_mins_ok.append(di_mins_all[i-1])
                    break
        return np.asarray(di_mins_ok)

    def extract_di_maxs(self, di_maxs_all):
        """Extract di maxima nearest to each u minimum."""
        di_maxs_ok = []
        for umin in self.u_mins:
            for i, imax in enumerate(di_maxs_all):
                if imax > umin:
                    if i == 0:
                        continue
                    # first to the right from u_min
                    di_maxs_ok.append(di_maxs_all[i])
                    break
        return np.asarray(di_maxs_ok)

    def spans(self, dt_range_te=None, dt_range_ne=(2, 2),
              sweep_direction='up'):
        """
        Provides corresponding spans for Te and ne

        Parameters
        ----------
        dt_range_te : tuple (float, float), optional
            Time shifts (left, right) in ms for span boundaries for Te.
            Default: None.
        dt_range_ne : tuple (float, float), optional
            Time shifts (left, right) in ms for span boundaries for ne.
            Default: (2, 2).
        mode : str, optional
            Span direction: 'up' (rising edge) or 'down' (falling edge).
            Default: 'up'.

        Returns
        -------
        tuple(ndarray, ndarray)
            tuple of two arrays.
            1 - array of (start, end) indices for Te spans.
            2 - array of (start, end) indices for ne spans.
        """
        spans_te = self.spans_te(dt_range=dt_range_te,
                                 sweep_direction=sweep_direction)
        spans_ne = self.spans_ne(dt_range=dt_range_ne)
        spans_te_len, spans_ne_len = len(spans_te), len(spans_ne)

        if spans_te_len == 0 or spans_ne_len == 0:
            raise ValueError("Empty span array detected")

        min_len = min(spans_te_len, spans_ne_len)
        return spans_te[:min_len], spans_ne[:min_len]

    def spans_te(self, dt_range=None, sweep_direction='up'):
        """
        Compute time spans for Te analysis.

        Parameters
        ----------
        dt_range : tuple (float, float), optional
            Time shifts (left, right) in ms for span boundaries. Default: None.
        sweep_direction : str, optional
            Span direction: 'up' (rising edge) or 'down' (falling edge).
            Default: 'up'.

        Returns
        -------
        ndarray
            Array of (start, end) indices for Te spans.
        """
        func_dict = {
            'up': self.te_dt_range_up,
            'down': self.te_dt_range_down
        }
        return func_dict[sweep_direction](dt_range)

    def te_dt_range_up(self, dt_range):
        """Compute Te spans on rising edge (using di maxima)."""
        spans = self.column_stack_arrays(self.u_mins, self.di_maxs)
        spans_te_dt_range = self.dt_mask(spans, dt_range)
        return spans_te_dt_range

    def te_dt_range_down(self, dt_range):
        """Compute Te spans on falling edge (using di minima)."""
        spans = self.column_stack_arrays(self.di_mins, self.u_mins)
        spans_te_dt_range = self.dt_mask(spans, dt_range)
        return spans_te_dt_range

    def spans_ne(self, dt_range=(2, 2)):
        """
        Compute time spans for ne analysis.

        Parameters
        ----------
        dt_range : tuple (float, float), optional
            Time shifts (left, right) in ms for span boundaries.
            Default: (2, 2).

        Returns
        -------
        ndarray
            Array of (start, end) indices for ne spans.
        """
        # adjust span boundaries by time shifts
        spans = self.column_stack_arrays(self.u_mins[0:-1],
                                         self.u_mins[1:])
        spans_ne = self.dt_mask(spans, dt_range)
        return spans_ne

    def shift_span_boundaries(self, span, left_shift, right_shift, id_max):
        """
        Adjusts span boundaries with shifts, handling edge cases.

        Rules:
        1. If either shift is None, apply only the other shift if valid
        2. If shifts would make left >= right, return original span
        3. If left shift is invalid (would go beyond limits), ignore it
        4. If right shift is invalid (would go beyond limits), ignore it
        5. If both shifts are invalid, return original span
        """
        l_old, r_old = span

        # Initialize new boundaries
        l_new = l_old
        r_new = r_old

        # Process left shift if specified
        if left_shift is not None:
            l_new = l_old + left_shift
            left_invalid = (l_new < 0) or (l_new > id_max) or (l_new >= r_old)
            if left_invalid:
                l_new = l_old  # Revert if invalid

        # Process right shift if specified
        if right_shift is not None:
            r_new = r_old - right_shift
            right_invalid = (r_new < 0) or (r_new > id_max) or (r_new <= l_old)
            if right_invalid:
                r_new = r_old  # Revert if invalid

        # Final validation
        if l_new >= r_new:
            return (l_old, r_old)  # Return original if boundaries cross

        return (l_new, r_new)

    def dt_mask(self, spans, dt_range):
        """Adjust span boundaries by time shifts."""

        if dt_range is None:
            return np.asarray(spans)

        # dt_left, dt_right оба направлены по уменьшению диапазона
        dt = self.t[1] - self.t[0]  # ELiseev advice
        # ELiseev advice
        id_left, id_right = int(dt_range[0]/dt), int(dt_range[1]/dt)
        id_max = len(self.t) - 1

        spans_shifted = []
        for span in spans:
            span_shifted = self.shift_span_boundaries(span, id_left,
                                                      id_right, id_max)
            spans_shifted.append(span_shifted)
        return np.asarray(spans_shifted)

    def column_stack_arrays(self, x, y):
        """ stacks two arrays even if lengths are different (by shortest) """
        return np.array(list(zip(x, y)))
