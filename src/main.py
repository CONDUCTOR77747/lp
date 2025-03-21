import numpy as np
import matplotlib.pyplot as plt
from load import load
from models import TeData
from processing import smooth
from plotting import create_interactive_plot

def raise_signals_above_zero(signals: dict, exceptions: list[str]=['time', 'LP.Power']) -> dict:
    signals_new = {}
    for signame, signal in signals.items():
        if signame in exceptions:
            signals_new[signame] = signal
            continue
        signal_min = min(signal)
        if signal_min < 0:
            signal -= signal_min
            signals_new[signame] = signal
    return signals_new

def main():
    # Load data
    signals = load("../configs/3727.yml")
    probe_name = 'LP.05'

    time = signals['time']
    U = signals['LP.Power']
    I = signals[probe_name]

    # Process data
    U_smooth = smooth(U, 9, 11)
    I_smooth = smooth(I, 3, 11)

    fig, ax = plt.subplots()
    ax.plot(time, U_smooth)
    ax.plot(time, I_smooth)

    # Initial parameters
    U_min, U_max = -100, 100
    n_avg = 3
    dt_left, dt_right = 1, -0.4
    fit = 'lin' # 'lin', 'exp'

    # Create TeData object
    Te_ = TeData(time, U_smooth, I_smooth, 71, dt_left, dt_right, U_min,
                 U_max, fit)

    # Create interactive plot
    create_interactive_plot(time, U, I, U_smooth, I_smooth, probe_name, Te_,
                            dt_left, dt_right, U_min, U_max, n_avg, fit, save_first=True, save_name='Te_3727_lp05.txt')
    plt.show()

if __name__ == '__main__':
    main()
