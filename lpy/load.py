# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:14:27 2025

@author: Ammosov

Module contains function to load
"""
# %% imports
from pathlib import Path
import yaml
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import resample
from nptdms import TdmsFile

# %% constants
GROUP = 'PXIe-6358'  # group name in tdms files (seems to be constant for now)
# %% funcs


def load(cfg_path: str) -> dict:
    """
    Load LP signals using config file.

    Parameters
    ----------
    cfg_path : str
        Path to config file.

    Returns
    -------
    signals: dict{np.ndarray, ...}
        Contains np.ndarray signals.

    Preferable keys for signals dictionary (useful for creating config file):
        - "time" is a time track in [ms]
        - "LP.Power" is a probe voltage in [V]
        - "LP.*" is a probe current in [mA], where * - number of a probe
    """
    cfg_path = str(Path(cfg_path).resolve())

    # load cfg file
    with open(cfg_path, encoding='utf-8') as stream:
        cfg = yaml.safe_load(stream)

    # get paths from cfg
    input_path = str(Path(cfg['tdms_path']).resolve())

    # create signals dict already factored
    signals = {}

    if 'bolometer' in cfg:
        bol_path = cfg['bolometer']['path']

        # load tdms file bolometer
        with TdmsFile.open(bol_path) as bol_file:
            bol_file = TdmsFile.read(bol_path)
        group_name = cfg['bolometer']['group']
        channel_name = cfg['bolometer']['channel']
        data_channel = bol_file[group_name][channel_name]
        signals['bolometer'] = data_channel[:]

    # load tdms file LP
    with TdmsFile.open(input_path) as tdms_file:
        tdms_file = TdmsFile.read(input_path)

    for signame, props in cfg['signals'].items():
        channel_name = props['channel']
        factor = props['factor']

        # get and factor signals from tdms
        data_channel = tdms_file[GROUP][channel_name]
        gain = data_channel.properties['GAIN']
        offset = data_channel.properties['Offset'] * 0.0

        data = (data_channel[:] * gain + offset) * eval(str(factor))
        signals[signame] = data

        # add time to signals dict
        if 'time' not in signals:
            rate = data_channel.properties['RATE']
            dt = 1 / rate
            t_len = len(signals[signame])
            time = np.linspace(0.0, (t_len * dt) * 1000, num=t_len)  # [ms]
            signals['time'] = time

            if 'bolometer' in signals:
                signals['bolometer'] = resample(signals['bolometer'],
                                                len(time))
                signals['bolometer'] = 150 * signals['bolometer'] / \
                    max(signals['bolometer'])
    return signals


# %%
if __name__ == '__main__':
    signals_load = load("../configs/3008.yml")
    signal = signals_load['LP.Power']
    plt.plot(signals_load['time'], signal)
    plt.grid()
