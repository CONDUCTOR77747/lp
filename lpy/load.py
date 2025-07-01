# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 17:14:27 2025

@author: Ammosov

Module contains function to load
"""
# %% imports
import re
import yaml
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import resample
from nptdms import TdmsFile

# %% constants
GROUP = 'PXIe-6358'  # group name in tdms files (seems to be constant for now)
# %% funcs

def extract_shot_number(file_path: str, prefix: str = "T15MD_",
                        postfix: str = ".tdms") -> int:
    """
    Extracts the shot number from a .tdms file path with the given prefix.

    Args:
        file_path (str): Full path to the .tdms file (e.g., "C:/data/T15MD_3162.tdms")
        prefix (str): Prefix before the shot number (default: "T15MD_")
        postfix (str): Postfix after the shot number (default: ".tdms")

    Returns:
        int: Extracted shot number

    Raises:
        ValueError: If no shot number is found or if the number is invalid
    """
    if file_path is None:
        return 0

    # Escape special regex characters in the prefix and construct pattern
    escaped_prefix = re.escape(prefix)
    pattern = rf"{escaped_prefix}(\d+){postfix}"

    match = re.search(pattern, file_path)
    if not match:
        return 0 # default error shot number
    try:
        return int(match.group(1))
    except ValueError:
        raise ValueError(f"Invalid shot number format: {match.group(1)}")

def load_text(cfg_path: str, cfg=None) -> dict:
    """ Load LP signals using config file but from txt """
    if cfg_path is not None:
        cfg_path = str(Path(cfg_path).resolve())
        # load cfg file
        with open(cfg_path, encoding='utf-8') as stream:
            cfg = yaml.safe_load(stream)
    elif cfg is None:
        raise ValueError("Ошибка в конфигурации")

    # get paths from cfg
    if 'path' not in cfg:
        raise ValueError("Отсутствует путь к файлу")
    input_path = str(Path(cfg['path']).resolve())

    # create signals dict already factored
    signals = {}

    signals['shot'] = extract_shot_number(input_path,  postfix=".txt")

    # load tdms file LP
    with open(input_path, 'r', encoding='utf-8') as f:
        headers = f.readline().strip().split()
        data = np.loadtxt('file.txt', skiprows=1)

    for signame, props in cfg['signals'].items():
        channel_name = props.get('channel')
        factor = props['factor']

        signals[signame] = data

        # add time to signals dict
        if 'time' not in signals:
            rate = data_channel.properties['RATE']
            dt = 1 / rate
            t_len = len(signals[signame])
            time = np.linspace(0.0, (t_len * dt) * 1000, num=t_len)  # [ms]
            signals['time'] = time

    return signals

def load(cfg_path: str, cfg=None) -> dict:
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
    if cfg_path is not None:
        cfg_path = str(Path(cfg_path).resolve())
        # load cfg file
        with open(cfg_path, encoding='utf-8') as stream:
            cfg = yaml.safe_load(stream)
    elif cfg is None:
        raise ValueError("Ошибка в конфигурации")

    # get paths from cfg
    if 'tdms_path' not in cfg:
        raise ValueError("Отсутствует путь к TDMS файлу")
    input_path = str(Path(cfg['tdms_path']).resolve())

    # create signals dict already factored
    signals = {}
    signals['shot'] = extract_shot_number(input_path)

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

    return signals


# %%
if __name__ == '__main__':
    signals_load = load("../configs/3008.yml")
    signal = signals_load['LP.Power']
    plt.plot(signals_load['time'], signal)
    plt.grid()
