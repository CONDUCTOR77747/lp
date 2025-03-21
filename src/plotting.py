import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor, TextBox, Button
import numpy as np
from models import TeData
from processing import (remove_negatives, exp_lp, remove_peaks_by_threshold,
                        remove_nans)
from nptdms import TdmsWriter, ChannelObject
from datetime import datetime

def plot_spans_with_limits(ax, spans, times, U, U_min, U_max):
    """Plot spans taking into account voltage limits U_min and U_max"""
    for span in spans:
        i0, i1 = span
        U_span = U[i0:i1]
        t_span = times[i0:i1]

        mask = (U_min < U_span) & (U_span < U_max)
        if not any(mask):
            continue

        valid_indices = np.where(mask)[0]
        if len(valid_indices) > 0:
            start_idx = valid_indices[0] + i0
            end_idx = valid_indices[-1] + i0
            ax.axvspan(times[start_idx], times[end_idx], color='yellow', alpha=0.3)

def save_tdms(filename, tt, TT, probe_name, properties):
    """Save TT data with time track to a TDMS file"""
    # Create channel for temperature data with associated time track
    properties['wf_starttime'] = 0  # Start time for the waveform
    properties['wf_increment'] = 1.0  # Placeholder, will be overridden by supplying tt

    temp_channel = ChannelObject(
        'LP',  # Group name
        f'{probe_name}',  # Channel name
        TT,  # Data
        properties,
        tt  # Time track directly associated with the data
    )

    # Write channel to TDMS file
    with TdmsWriter(filename) as tdms_writer:
        tdms_writer.write_segment([temp_channel])

def get_Te_data(Te_, n_avg):
    tt, TT, info = Te_.avg_Te(1, n_avg)
    tt, TT = remove_negatives(tt, TT, mode='zero')
    tt, TT = remove_peaks_by_threshold(tt, TT, 300, mode='zero')
    tt, TT = remove_nans(tt, TT, mode='zero')
    return tt, TT

def create_interactive_plot(times, U, I, U_smooth, I_smooth, probe_name, Te_,
                            dt_left, dt_right, U_min, U_max, n_avg, fit, save_first=False, save_name=None):

    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True)

    # Create MultiCursor as a nonlocal variable
    multi = [None]  # Use list to store reference that can be modified in nested function

    def mouse_click(event):
        if not ('ctrl' in event.modifiers):
            return

        i = Te_.find_nearest_info(event.xdata)

        try:
            central_span = Te_.Te_spans[i]
            info = Te_.info[i]
            if fit == 'lin':
                tt, U, I, k, c, rvalue, pvalue, kerr, cerr, U_wide, I_wide = info
            elif fit == 'exp':
                tt, U, I, k, c, U_wide, I_wide = info

            fig_detail, ax_detail = plt.subplots()

            if Te_.fit == 'lin':
                ax_detail.plot(U_wide, np.log(I_wide), 'o', alpha=0.2)
                ax_detail.plot(U, np.log(I), 'o', ms=5)
                ax_detail.plot(U, U*k + c)
            elif Te_.fit == 'exp':
                ax_detail.plot(U_wide, I_wide, 'o', alpha=0.2)
                ax_detail.plot(U, I, 'o', ms=5)
                xxx = np.linspace(0.0, 100.0)
                #ax.plot(U, exp_lp( U*k + c, 1, 0) )
                ax_detail.plot(xxx, exp_lp( xxx, k, c) )

            t = Te_.t[central_span[0]:central_span[1]].mean()
            ax_detail.set_title(f't = {int(t)}   Te = {int(1/k)}')
            ax_detail.grid(True)
            plt.show()

        except Exception as e:
            print('error info')
            print(e)

    def update(val):
        try:
            nonlocal Te_
            new_umin = float(text_umin.text)
            new_umax = float(text_umax.text)
            new_dtl = float(text_dtl.text)
            new_dtr = float(text_dtr.text)
            new_navg = int(text_navg.text)

            # Store old cursor visibility state
            cursor_visible = multi[0].visible if multi[0] is not None else True

            ax1.clear()
            ax2.clear()

            ax1.plot(times, U, label='Voltage, U')
            ax1.plot(times, I, label=f'{probe_name}, mA')
            ax1.plot(times, Te_.U_smooth, label='U smooth')
            ax1.plot(times, Te_.dI, label='dI')
            ax1.plot(times, Te_.sin_abs, label='abs sin')
            ax1.set_ylabel('Voltage, U; Probe Current, mA')
            ax1.legend(loc='upper right')
            ax1.grid()

            Te_ = TeData(times, U_smooth, I_smooth, 71, new_dtl, new_dtr, new_umin, new_umax, fit)
            tt, TT = get_Te_data(Te_, new_navg)

            ax2.plot(tt, TT, 'o', color='g')
            ax2.set_xlabel('t, ms')
            ax2.set_ylabel('Te, eV')
            ax2.grid()

            plot_spans_with_limits(ax1, Te_.Te_spans, times, U_smooth, new_umin, new_umax)

            # Update MultiCursor
            multi[0] = MultiCursor(fig.canvas, (ax1, ax2), color='r', lw=1)
            multi[0].visible = cursor_visible

            plt.draw()

        except ValueError:
            print("Please enter valid numbers")



    # Initial plot
    tt, TT = get_Te_data(Te_, n_avg)

    ax1.plot(times, U, label='Voltage, U')
    ax1.plot(times, I, label=f'{probe_name}, mA')
    ax1.plot(times, Te_.U_smooth, label='U smooth')
    ax1.plot(times, Te_.dI, label='dI')
    ax1.plot(times, Te_.sin_abs, label='abs sin')
    ax1.set_ylabel('Voltage, U; Probe Current, mA')
    ax1.legend(loc='upper right')
    ax1.grid()

    ax2.plot(tt, TT, 'o', color='g')
    ax2.set_xlabel('t, ms')
    ax2.set_ylabel('Te, eV')
    ax2.grid()

    plot_spans_with_limits(ax1, Te_.Te_spans, times, U_smooth, U_min, U_max)

    # Add text boxes
    axbox_umin = plt.axes([0.15, 0.01, 0.05, 0.03])
    axbox_umax = plt.axes([0.25, 0.01, 0.05, 0.03])
    axbox_dtl = plt.axes([0.35, 0.01, 0.05, 0.03])
    axbox_dtr = plt.axes([0.45, 0.01, 0.05, 0.03])
    axbox_navg = plt.axes([0.55, 0.01, 0.05, 0.03])
    text_umin = TextBox(axbox_umin, 'Umin ', initial=str(U_min))
    text_umax = TextBox(axbox_umax, 'Umax ', initial=str(U_max))
    text_dtl = TextBox(axbox_dtl, 'dtl ', initial=str(dt_left))
    text_dtr = TextBox(axbox_dtr, 'dtr ', initial=str(dt_right))
    text_navg = TextBox(axbox_navg, 'n ', initial=str(n_avg))

    # Connect events
    text_umin.on_submit(update)
    text_umax.on_submit(update)
    text_dtl.on_submit(update)
    text_dtr.on_submit(update)
    text_navg.on_submit(update)
    fig.canvas.mpl_connect('button_press_event', mouse_click)

    # Initialize MultiCursor
    multi[0] = MultiCursor(fig.canvas, (ax1, ax2), color='r', lw=1)

    if save_first:
        if save_name is None:
            # Format: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"Te_{timestamp}.txt"
        # Stack xx and yy column-wise
        data = np.column_stack((tt, TT))
        # Save to a text file
        np.savetxt(save_name, data, fmt='%.2f', delimiter='\t',
                   header='t\tTe', comments='')

    return fig, (ax1, ax2)
