# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:08:25 2025

@author: Ammosov

Testing load module
"""
import pytest
import numpy as np
from lpy import load, extract_shot_number

def test_extract_shot_number():
    """ Test extract_shot_number function (gets shot numbert from str) """
    # case 1 standart
    assert 3008 == extract_shot_number("test_data/T15MD_3008.tdms")
    # case 2 standart
    assert 12345 == extract_shot_number("test_data/T15MD_12345.tdms")
    # case 3 new postfix and prefix
    prefix = '12345test'
    postfix = 'test12345'
    test_str = '12345test12345test12345'
    assert 12345 == extract_shot_number(test_str, prefix=prefix,
                                       postfix=postfix)
    # case 4 invalid input
    assert 0 == extract_shot_number("test_data/T15MD_.tdms")
    assert 0 == extract_shot_number("")
    assert 0 == extract_shot_number(None)


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
    assert signals['shot'] == 3008


if __name__ == "__main__":
    pytest.main(["test_lpy_load.py"])
