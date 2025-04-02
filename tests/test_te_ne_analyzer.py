# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 17:05:54 2025

@author: Student
"""

import pytest
import numpy as np
from scipy.constants import physical_constants
from lpy import load, TeNeAnalyzer, SpanDetector


@pytest.fixture
def sample_data():
    """Load Langmuir probe data for testing."""
    signals = load("test_data/3008.yml")
    t = signals['time']
    u = signals['LP.Power']
    i = signals['LP.13']
    return t, u, i


def test_init(sample_data):
    """ Test TeNeAnalyzer initialization main params. """
    t, u, i = sample_data
    tna = TeNeAnalyzer(t, u, i)
    assert np.array_equal(tna.t, t)
    assert np.array_equal(tna.u, u)
    assert np.array_equal(tna.i, i)

def test_u_mask(sample_data):
    t, u, i = sample_data
    tna = TeNeAnalyzer(t, u, i)
    # case 1 u_range is None
    u_new, i_new = tna.u_mask(u, i, None)
    assert np.array_equal(u_new, u) and np.array_equal(i_new, i)
    # case 2 standard
    u_new, i_new = tna.u_mask(u, i, u_range=(0, 10))
    assert np.isclose(np.min(u_new), 0, atol=0.1)
    assert np.isclose(np.max(u_new), 10, atol=0.1)
    # case 3 standard
    u_new, i_new = tna.u_mask(u, i, u_range=(2.5, 8.7))
    assert np.isclose(np.min(u_new), 2.5, atol=0.1)
    assert np.isclose(np.max(u_new), 8.7, atol=0.1)

def test_ne_formula(sample_data):
    t, u, i = sample_data
    tna = TeNeAnalyzer(t, u, i)
    # case 1 standart
    m_i = physical_constants['proton mass in u'][0]
    probe_area = np.sin(np.deg2rad(15)) * np.pi*(5)**2/4
    ne = tna.ne_formula(24, 34, probe_area, m_i)
    assert np.isclose(ne, 1.53, atol=0.01)
    # case 2 invalid input te, i_is = 0
    ne = tna.ne_formula(0, 0, probe_area, m_i)
    assert np.isclose(ne, 0)
    # case 2.1 invalid input te < 0
    ne = tna.ne_formula(-1, 0, probe_area, m_i)
    assert np.isclose(ne, 0)
    # case 3 invalid input te, probe_area = np.nan
    ne = tna.ne_formula(np.nan, np.nan, probe_area, m_i)
    assert np.isclose(ne, 0)
    # case 4 invalid input te, probe_area = None
    ne = tna.ne_formula(None, None, probe_area, m_i)
    assert np.isclose(ne, 0)

# def test_calc_te

if __name__ == '__main__':
    pytest.main(["test_te_ne_analyzer.py"])
