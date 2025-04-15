# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 17:05:54 2025

@author: Student
"""

import pytest
import numpy as np
from scipy.constants import physical_constants
from lpy import load, TeNeAnalyzer, PROBE_AREA_DEFAULT


@pytest.fixture
def _sample_data():
    """Load Langmuir probe data for testing."""
    signals = load("test_data/3008.yml")
    t = signals['time']
    u = signals['LP.Power']
    i = signals['LP.13']
    return t, u, i


@pytest.fixture
def _sample_data_probe_9():
    """Load Langmuir probe data for testing."""
    signals = load("test_data/3008.yml")
    t = signals['time']
    u = signals['LP.Power']
    i = signals['LP.09']
    return t, u, i


def test_init(_sample_data):
    """ Test TeNeAnalyzer initialization main params. """
    t, u, i = _sample_data
    tna = TeNeAnalyzer(t, u, i)
    assert np.array_equal(tna.t, t)
    assert np.array_equal(tna.u, u)
    assert np.array_equal(tna.i, i)


def test_u_mask(_sample_data):
    """ Test u_mask method (filters data by voltage) """
    t, u, i = _sample_data
    tna = TeNeAnalyzer(t, u, i)

    # case 1 u_range is None
    # pylint: disable=protected-access
    u_new, i_new = tna._u_mask(u, i, None)
    assert np.array_equal(u_new, u) and np.array_equal(i_new, i)

    # case 2 base
    # pylint: disable=protected-access
    u_new, i_new = tna._u_mask(u, i, u_range=(0, 10))
    assert np.isclose(np.min(u_new), 0, atol=0.1)
    assert np.isclose(np.max(u_new), 10, atol=0.1)

    # case 3 base
    # pylint: disable=protected-access
    u_new, i_new = tna._u_mask(u, i, u_range=(2.5, 8.7))
    assert np.isclose(np.min(u_new), 2.5, atol=0.1)
    assert np.isclose(np.max(u_new), 8.7, atol=0.1)


def test_ne_formula(_sample_data):
    """ Test ne formula method (formula for calculation ne) """
    t, u, i = _sample_data
    tna = TeNeAnalyzer(t, u, i)

    # case 1 standart
    m_i = physical_constants['proton mass in u'][0]
    probe_area = np.sin(np.deg2rad(15)) * np.pi*(5)**2/4
    # pylint: disable=protected-access
    ne = tna._ne_formula(24, 34, probe_area, m_i)
    assert np.isclose(ne, 1.53, atol=0.01)

    # case 2 invalid input te, i_is = 0
    # pylint: disable=protected-access
    ne = tna._ne_formula(0, 0, probe_area, m_i)
    assert np.isclose(ne, 0)

    # case 3 invalid input te < 0
    # pylint: disable=protected-access
    ne = tna._ne_formula(-1, 0, probe_area, m_i)
    assert np.isclose(ne, 0)

    # case 4 invalid input te, probe_area = np.nan
    # pylint: disable=protected-access
    ne = tna._ne_formula(np.nan, np.nan, probe_area, m_i)
    assert np.isclose(ne, 0)

    # case 5 invalid input te, probe_area = None
    # pylint: disable=protected-access
    ne = tna._ne_formula(None, None, probe_area, m_i)
    assert np.isclose(ne, 0)


def test_te_ne_analyzer_probe_13(_sample_data):
    """ Test calc_te_ne method on expected output. Test data probe 13 """
    t, u, i = _sample_data
    tna = TeNeAnalyzer(t, u, i)
    # case 1 default params
    res_t, te, ne, info = tna.calc_te_ne()
    u_mins_len = len(tna.spandet.u_mins)
    # lens by math: u_mins-1 = spans_ne; te (n_avg=1) = u_mins-1 (sliding win.)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-1 == 248
    assert np.isclose(te.mean(), 18.1, atol=0.1)
    assert np.isclose(ne.mean(), 0.37, atol=0.1)

    # case 2 linear fit
    # prepare parameters for calc_te_ne
    parameters = {
        'n_avg': 3,
        'dt_range_te': (0, 0),
        'probe_area': PROBE_AREA_DEFAULT,
        'u_range': (0, 15),
        'dt_range_ne': (2, 2),
        'sweep_direction': 'up',
        'fit_method': 'linear'
        }
    res_t, te, ne, info = tna.calc_te_ne(parameters)

    u_mins_len = len(tna.spandet.u_mins)
    # lens by math: u_mins-1 = spans_ne; te (n_avg=3) = u_mins-3 (sliding win.)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-3 == 246
    assert np.isclose(te.mean(), 6.2, atol=0.1)
    assert np.isclose(ne.mean(), 0.6, atol=0.1)

    # case 3 exponential fit
    # prepare parameters for calc_te_ne
    parameters = {
        'n_avg': 3,
        'dt_range_te': (0, 0),
        'probe_area': PROBE_AREA_DEFAULT,
        'u_range': (0, 15),
        'dt_range_ne': (2, 2),
        'sweep_direction': 'up',
        'fit_method': 'exponential'
        }
    res_t, te, ne, info = tna.calc_te_ne(parameters)

    u_mins_len = len(tna.spandet.u_mins)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-3 == 246
    assert np.isclose(te.mean(), 4.5, atol=0.1)
    assert np.isclose(ne.mean(), 0.6, atol=0.1)


def test_te_ne_analyzer_probe_9(_sample_data_probe_9):
    """ Test calc_te_ne method on expected output. Test data probe 9 """
    t, u, i = _sample_data_probe_9
    tna = TeNeAnalyzer(t, u, i)

    # case 1 default params
    res_t, te, ne, info = tna.calc_te_ne()
    u_mins_len = len(tna.spandet.u_mins)
    # lens by math: u_mins-1 = spans_ne; te (n_avg=3) = u_mins-3 (sliding win.)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-1 == 248
    assert np.isclose(te.mean(), 21.2, atol=0.1)
    assert np.isclose(ne.mean(), 0.8, atol=0.1)

    # case 2 linear fit
    # prepare parameters for calc_te_ne
    parameters = {
        'n_avg': 1,
        'dt_range_te': (0, 0),
        'probe_area': PROBE_AREA_DEFAULT,
        'u_range': (0, 15),
        'dt_range_ne': (2, 2),
        'sweep_direction': 'up',
        'fit_method': 'linear'
        }
    res_t, te, ne, info = tna.calc_te_ne(parameters)

    u_mins_len = len(tna.spandet.u_mins)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-1 == 248
    assert np.isclose(te.mean(), 6.2, atol=0.1)
    assert np.isclose(ne.mean(), 1.2, atol=0.1)

    # case 3 exponential fit
    # prepare parameters for calc_te_ne
    parameters = {
        'n_avg': 1,
        'dt_range_te': (0, 0),
        'probe_area': PROBE_AREA_DEFAULT,
        'u_range': (0, 15),
        'dt_range_ne': (2, 2),
        'sweep_direction': 'up',
        'fit_method': 'exponential'
        }
    res_t, te, ne, info = tna.calc_te_ne(parameters)

    u_mins_len = len(tna.spandet.u_mins)
    assert len(res_t) == len(te) == len(ne) == len(info) == u_mins_len-1 == 248
    assert np.isclose(te.mean(), 5.3, atol=0.1)
    assert np.isclose(ne.mean(), 1.1, atol=0.1)


if __name__ == '__main__':
    pytest.main(["test_lpy_te_ne_analyzer.py"])
