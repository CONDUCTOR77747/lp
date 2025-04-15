"""
Author: Ammosov
Langmuir probe analysis
Main file to launch a program

Example:
    from lpy import load, TeNeAnalyzer
    tna = TeNeAnalyzer(t, u, i)
    te_t, te, ne, info = tna.calc_te_ne(
        n_avg=3,
        dt_range_te=(0,0),
        probe_area=np.pi*(5)**2/4*np.sin(np.deg2rad(15)),
        u_range=(0, 15),
        dt_range_ne=(2,2),
        sweep_direction='up',
        fit_method='linear'
        )
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor
from lpy import (load, smooth, TeNeAnalyzer, remove_negatives,
                 remove_peaks_by_threshold)

if __name__ == '__main__':
    # Load data
    signals = load("configs/3008_home.yml")
    probe_name = 'LP.13'
    shot = signals['shot']

    t = signals['time']
    u = signals['LP.Power']
    i = signals[probe_name]

    # smooth data for processing
    # u = smooth(u, 9, 11)
    # i = smooth(i, 3, 11)

    tna = TeNeAnalyzer(t, u, i)
    parameters = {
        'n_avg': 1,
        'dt_range_te': (0, 0),
        'u_range': (0, 15),
        'dt_range_ne': (2, 2),
        'sweep_direction': 'up',
        'fit_method': 'exponential',
        'te_threshold': 40,
        }
    res_t, te, ne, info = tna.calc_te_ne(parameters)

    # te_t, te = remove_peaks_by_threshold(te_t, te, 150, mode='zeros')

#%%
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, sharex=True,
                                        constrained_layout=True)
    # ax1
    ax1.plot(t, u, label='Voltage, V')
    ax1.plot(t, i, label=f'{probe_name}, mA')
    # ax1.plot(t, tna.spandet.u_smooth, label='Voltage smoothed, V')
    # ax1.plot(t, tna.spandet.di, label='Probe Current Gradient')
    ax1.set_ylabel('Voltage, U; Probe Current, mA')
    ax1.set_title(f'#{shot}')
    ax1.legend(loc='upper right')
    ax1.grid()
    for span in tna.spans_te:
        ax1.axvspan(t[span[0]], t[span[1]], color='green', alpha=0.2)

    for span in tna.spans_ne:
        ax1.axvspan(t[span[0]], t[span[1]], color='red', alpha=0.2)

    # ax2
    ax2.plot(res_t, te, 'o', color='green')
    ax2.set_ylabel('Te, eV')
    # te_errs = [kerr/k**2 for k, _, kerr, _ in info]
    # ax2.errorbar(te_t, te, yerr=te_errs, fmt='o', ecolor='black', capsize=5, color='green')
    ax2.grid()

    # ax3
    ax3.plot(res_t, ne, 'o', color='red')
    ax3.set_xlabel('t, ms')
    ax3.set_ylabel('ne, 10^18 m^-3')
    ax3.grid()

    multic = MultiCursor(fig.canvas, (ax1, ax2, ax3), color='r', lw=1)
    plt.show()
