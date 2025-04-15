# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 16:32:53 2025

@author: Ammosov
"""

import pytest
import numpy as np
from lpy import SpanDetector, load


@pytest.fixture
def _sample_data():
    """Load Langmuir probe data for testing."""
    signals = load("test_data/3008.yml")
    t = signals['time']
    u = signals['LP.Power']
    i = signals['LP.13']
    return t, u, i


def mean_diff_spans(t, spans1, spans2):
    """
    Calculates mean difference between two span arrays
    Parameters
    ----------
    t : array like
        time values in [ms].
    spans1 : np.array[(float, float), ...]
        First array of spans.
    spans2 : np.array[(float, float), ...]
        Second array of spans..

    Returns
    -------
    float
        Mean difference between two span arrays.
    """
    span_diff = []
    for i, j in zip(spans1, spans2):
        span_diff.append(abs(t[i]-t[j]))
    return np.asarray(span_diff).mean()


def test_init(_sample_data):
    """Test SpanDetector initialization main params."""
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    assert np.array_equal(detector.t, t)
    assert np.array_equal(detector.u, u)
    assert np.array_equal(detector.i, i)


def test_calc_repere_points(_sample_data):
    """Test detection of u minima and di extrema."""
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    assert np.isclose(len(detector.u_mins), 249, atol=1.0)
    assert np.isclose(np.diff(t[detector.u_mins]).mean(), 10, atol=1.0)
    assert np.isclose(len(detector.u_mins), 249, atol=1.0)
    assert np.isclose(len(detector.u_mins), 249, atol=1.0)
    assert np.isclose(len(detector.di_mins), 249, atol=1.0)
    assert np.isclose(len(detector.di_maxs), 249, atol=1.0)


def test_column_stack_arrays(_sample_data):
    """ Test column_stack_array method """
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    arr1 = np.zeros(10)
    arr2 = np.ones(10)
    arr3 = np.zeros(11)
    # pylint: disable=protected-access
    res1 = detector._column_stack_arrays(arr1, arr2)
    # pylint: disable=protected-access
    res2 = detector._column_stack_arrays(arr3, arr2)
    assert len(res1) == 10
    assert len(res2) == 10
    assert np.array_equal(res1, np.column_stack((arr1, arr2)))
    assert np.array_equal(res2, np.column_stack((arr1, arr2)))


def test_spans_te_up(_sample_data):
    """Test Te span detection (rising edge mode)."""
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    spans = detector.spans_te(dt_range=None, sweep_direction='up')
    assert spans.ndim == 2
    assert spans.shape[1] == 2
    # pylint: disable=protected-access
    spans_new = detector._column_stack_arrays(
        detector.u_mins, detector.di_maxs)
    assert np.array_equal(spans, spans_new)


def test_spans_te_down(_sample_data):
    """Test Te span detection (falling edge mode)."""
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    spans = detector.spans_te(dt_range=None, sweep_direction='down')
    assert spans.ndim == 2
    assert spans.shape[1] == 2
    # pylint: disable=protected-access
    spans_new = detector._column_stack_arrays(
        detector.di_mins, detector.u_mins)
    assert np.array_equal(spans, spans_new)


def test_shift_span_boundaries(_sample_data):
    """ Test time shifting spans boundaries LOGIC method """
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    span = (20000, 30000)
    id_max = 50000

    # case 1 a reasonable input
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 4000, 4000, id_max)
    assert l == 24000 and r == 26000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, -4000, 4000, id_max)
    assert l == 16000 and r == 26000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 4000, -4000, id_max)
    assert l == 24000 and r == 34000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, -4000, -4000, id_max)
    assert l == 16000 and r == 34000

    # case 2 a input to make span with zero length
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 5000, 5000, id_max)
    assert l == 20000 and r == 30000

    # case 3 a reasonable input from left only
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 4000, 1e6, id_max)
    assert l == 24000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 4000, -1e6, id_max)
    assert l == 24000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 4000, None, id_max)
    assert l == 24000 and r == 30000

    # case 4 a reasonable input from right only
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 1e6, 4000, id_max)
    assert l == 20000 and r == 26000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, -1e6, 4000, id_max)
    assert l == 20000 and r == 26000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, None, 4000, id_max)
    assert l == 20000 and r == 26000

    # case 5 both shifts are invalid
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 1e6, 1e6, id_max)
    assert l == 20000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, -1e6, 1e6, id_max)
    assert l == 20000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, 1e6, -1e6, id_max)
    assert l == 20000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, -1e6, -1e6, id_max)
    assert l == 20000 and r == 30000
    # pylint: disable=protected-access
    l, r = detector._shift_span_boundaries(span, None, None, id_max)
    assert l == 20000 and r == 30000


def test_dt_mask(_sample_data):
    """ Test time shifting spans boundaries """
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    spans = detector.spans_te(dt_range=None)

    # case 1 a reasonable dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (0.01, 0.01))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.01, atol=0.005)
    assert len(spans) == len(spans_dt)

    # case 2 a reasonable dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (0.05, 0.05))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.05, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 3 a reasonable dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (0.23, 0.23))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert len(spans) == len(spans_dt)
    # check one particular span in real meaningful data
    for span, span_dt in zip(spans, spans_dt):
        if np.isclose(t[span[0]], 780, atol=5.0):
            assert np.isclose(abs(t[span[0]]-t[span_dt[0]]), 0.23, atol=0.01)
            assert np.isclose(abs(t[span[1]]-t[span_dt[1]]), 0.23, atol=0.01)
            break

    # case 4 a way big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (1e6, 1e6))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.0, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 5 a way big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (-1e6, 1e6))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.0, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 6 a way big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (1e6, -1e6))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.0, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 7 a way big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (-1e6, -1e6))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.0, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 8 a bit big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (20, 20))
    diff = mean_diff_spans(t, spans, spans_dt)
    assert np.isclose(diff, 0.0, atol=0.01)
    assert len(spans) == len(spans_dt)

    # case 9 a bit big dt_range
    # pylint: disable=protected-access
    spans_dt = detector._dt_mask(spans, (3, -3))
    assert len(spans) == len(spans_dt)
    lefts, rights = spans_dt.T[0], spans_dt.T[1]
    # lefts must be the same bc left border > r_old border
    assert np.allclose(lefts, spans.T[0])
    # right borders must shift on 3
    mean_abs_diff = np.mean(np.abs(t[rights] - t[spans.T[1]]))
    assert np.isclose(mean_abs_diff, 3, atol=0.1)


def test_spans_ne(_sample_data):
    """Test ne span detection."""
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    spans = detector.spans_ne(dt_range=(0, 0))
    assert spans.ndim == 2
    assert spans.shape[1] == 2
    assert len(detector.u_mins) == len(spans) + 1

    # case 1 dt_range None
    spans_new = detector.spans_ne(dt_range=None)
    assert np.array_equal(spans, spans_new)

    # case 2 no dt_range
    # pylint: disable=protected-access
    spans_new = detector._column_stack_arrays(detector.u_mins[0:-1],
                                              detector.u_mins[1:])
    assert np.array_equal(spans, spans_new)

    # case 3 a reasonable dt_range
    spans_new = detector.spans_ne(dt_range=(1.5, 1.5))
    diff = mean_diff_spans(t, spans, spans_new)
    assert np.isclose(diff, 1.5, atol=0.1)
    assert len(spans) == len(spans_new)


def test_te_ne_spans_for_consistency(_sample_data):
    """ Test te and ne span arrays if their elements are
    sequentially consistent aka testing spans method """
    t, u, i = _sample_data
    detector = SpanDetector(t, u, i)
    spans_te, spans_ne = detector.spans()
    assert len(spans_te) == len(spans_ne)
    for span_te, span_ne in zip(spans_te, spans_ne):
        assert span_te[0] < span_te[1] < span_ne[0] < span_ne[1]


if __name__ == '__main__':
    pytest.main(['test_lpy_span_detector.py'])
