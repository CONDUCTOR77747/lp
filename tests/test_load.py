# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:08:25 2025

@author: Ammosov

Testing load module
"""
import pytest
import numpy as np
from lpy import load


def test_load():
    """ Testing load function in comparison to manually prepared txts """
    test_data_path = "test_data/"
    signals = load(test_data_path+"3008.yml")

    time_txt = np.loadtxt(test_data_path+"3008_LP.Power.txt").T[0]
    u_txt = np.loadtxt(test_data_path+"3008_LP.Power.txt").T[1] * -34
    u_txt_9 = np.loadtxt(test_data_path+"3008_LP.09.txt").T[1] * 1000 / 50
    u_txt_13 = np.loadtxt(test_data_path+"3008_LP.13.txt").T[1] * 1000 / 100

    assert len(signals['time']) == len(time_txt)
    assert np.allclose(signals['time'], time_txt, atol=0.01)
    assert np.allclose(signals['LP.Power'], u_txt, atol=0.1)
    assert np.allclose(signals['LP.09'], u_txt_9, atol=0.1)
    assert np.allclose(signals['LP.13'], u_txt_13, atol=0.1)


if __name__ == "__main__":
    pytest.main()
