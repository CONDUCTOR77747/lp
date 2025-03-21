import numpy as np
from scipy.stats import linregress
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve, argrelextrema, find_peaks

def smooth(y, avg, n=1):
    y_smooth = y
    for i in range(n+1):
        box = np.ones(avg)/avg
        y_smooth = fftconvolve(y_smooth, box, mode='same')
    return y_smooth

def detect_peaks_IQR(data, q1=25, q3=75):
    Q1 = np.percentile(data, q1)
    Q3 = np.percentile(data, q3)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    spike_indices = np.where((data < lower_bound) | (data > upper_bound))[0]
    return spike_indices

def remove_peaks_IQR(tt, TT, q1=25, q3=75, mode="mask"):
    peaks_idx = detect_peaks_IQR(TT, q1=q1, q3=q3)
    if mode == "zero":
        TT[peaks_idx] = 0.0
    elif mode == "mask":
        mask = np.ones_like(TT, dtype=bool)
        mask[peaks_idx] = False
        tt = tt[mask]
        TT = TT[mask]
    return tt, TT

def remove_nans(tt, TT, mode="mask"):
    if mode == "zero":
        TT[np.isnan(TT)] = 0.0
    elif mode == "mask":
        mask = ~np.isnan(TT)
        tt = tt[mask]
        TT = TT[mask]
    return tt, TT

def remove_negatives(tt, TT, mode="mask"):
    if mode == "zero":
        TT[TT <= 0] = 0.0
    elif mode == "mask":
        mask = (TT > 0)
        tt = tt[mask]
        TT = TT[mask]
    return tt, TT

def remove_peaks_by_threshold(tt, TT, threshold, mode="mask"):
    """
    Removes peaks from TT based on a specified threshold.

    Parameters:
    tt (array-like): Time or index array corresponding to TT.
    TT (array-like): Data array from which peaks are to be removed.
    threshold (float): Threshold value to identify peaks.
    mode (str): Mode of operation, either "zero" or "mask".

    Returns:
    tuple: Modified tt and TT arrays.
    """
    # Identify peaks based on the threshold
    peaks_idx = np.where(TT > threshold)[0]

    if mode == "zero":
        # Set peaks to zero
        TT[peaks_idx] = 0.0
    elif mode == "mask":
        # Create a mask to remove peaks
        mask = np.ones_like(TT, dtype=bool)
        mask[peaks_idx] = False
        tt = tt[mask]
        TT = TT[mask]

    return tt, TT

def exp_lp(x, k, c):
    return np.exp(k*x + c)

def sin_abs_wave(t, A, f, phi, shift):
    return np.abs(A * np.sin(np.pi * f * t + phi/np.pi)) - shift

def sin_abs_wave_fixed_shift(t, A, f, phi):
    shift = 30
    return np.abs(A * np.sin(np.pi * f * t + phi/np.pi)) - shift

def get_left_boundary_analytical(times, U_smooth, debug=False):
    """ get left boundary of the pulse from the smooth U(t) using abs sin wave fit """
    # popt, _ = curve_fit(sin_abs_wave, times, U_smooth, p0=[310, 0.1, 9.7, 40])
    # A_fit, f_fit, phi_fit, shift_fit = popt
    # sin_abs = sin_abs_wave(times, A_fit, f_fit, phi_fit, shift_fit)

    popt, _ = curve_fit(sin_abs_wave_fixed_shift, times, U_smooth, p0=[210, 0.1, 9.7])
    A_fit, f_fit, phi_fit = popt
    sin_abs = sin_abs_wave_fixed_shift(times, A_fit, f_fit, phi_fit)

    zero_crossings = np.where(np.diff(np.sign(sin_abs)))[0]
    diffs = np.diff(zero_crossings)
    even = False
    if diffs[0] < diffs[1]:
        even = True
    left_cross = zero_crossings[0::2]
    right_cross = zero_crossings[1::2]
    if not even:
       left_cross, right_cross = right_cross, left_cross

    if debug:
        return right_cross, sin_abs
    else:
        return right_cross

# abs sin di max

# def calc_spanlist(time, U, I, Ksmooth, dt_left, dt_right, debug=False):
#     dt = time[1] - time[0]
#     di_left = int(dt_left/dt)
#     di_right = int(dt_right/dt)

#     U_smooth = smooth(U, 9, 11)
#     I_smooth = smooth(I, Ksmooth, 11)
#     dI = np.gradient(I_smooth)
#     dI = smooth(dI, Ksmooth, 11)

#     U_minimums, sin_abs = get_left_boundary_analytical(time, U_smooth, debug=True)
#     dI_maximums = argrelextrema(dI, np.greater)[0]

#     time_len = len(time)
#     dI_maximums_ok = []
#     for idx in U_minimums:
#         idx_maximums = dI_maximums - idx
#         idx_maximums[idx_maximums < 0] = time_len + 1000000
#         i = np.min(idx_maximums)
#         if i+idx >= time_len:
#             break
#         dI_maximums_ok.append(i + idx)

#     spanlist = []
#     for i0, i1 in zip(U_minimums, dI_maximums_ok):
#         spanlist.append((i0 + di_left, i1-di_right))

#     if debug:
#         return spanlist, U_smooth, dI, sin_abs
#     else:
#         return spanlist

# standart u min di max

def calc_spanlist(time, U, I, Ksmooth, dt_left, dt_right, debug=False):
    # dt_left, dt_right оба направлены на уменьшение диапазона
    dt = time[1] - time[0]
    di_left = int(dt_left/dt)
    di_right = int(dt_right/dt)

    U_smooth = smooth(U, 151, 11)
    # dU = np.gradient(U_smooth)
    # dU = smooth(dU, 151, 11)

    I_smooth = smooth(I, Ksmooth, 11)
    dI = np.gradient(I_smooth)
    dI = smooth(dI, Ksmooth, 11)

    U_minimums = argrelextrema(U_smooth, np.less)
    dI_maximums = argrelextrema(dI, np.greater)

    U_minimums = U_minimums[0] # np.asarray(dU_minimums)
    dI_maximums = dI_maximums[0] # np.asarray(dI_minimums)


    dI_maximums_ok = []
    for idx in U_minimums:
        # расстояние от минимумов dI до текущего максимума dU
        idx_maximums = dI_maximums - idx

        idx_maximums[idx_maximums < 0] = 1000000

        # Ближайший минимум dI после текущего максимума dU
        i = np.min(idx_maximums)

        dI_maximums_ok.append(i + idx)

    spanlist = []
    for i0, i1 in zip(U_minimums, dI_maximums_ok):
        spanlist.append( (i0 + di_left, i1-di_right) )

    if debug:
        return spanlist, U_smooth, dI, dI*500
    else:
        return spanlist

# di min U min
# def calc_spanlist(time, U, I, Ksmooth, dt_left, dt_right, debug=False):
#     # dt_left, dt_right оба направлены на уменьшение диапазона
#     dt = time[1] - time[0]
#     di_left = int(dt_left/dt)
#     di_right = int(dt_right/dt)

#     U_smooth = smooth(U, 151, 11)
#     # dU = np.gradient(U_smooth)
#     # dU = smooth(dU, 151, 11)

#     I_smooth = smooth(I, Ksmooth, 11)
#     dI = np.gradient(I_smooth)
#     dI = smooth(dI, Ksmooth, 11)

#     U_minimums = argrelextrema(U_smooth, np.less)
#     dI_maximums = argrelextrema(dI*-1, np.greater)

#     U_minimums = U_minimums[0] # np.asarray(dU_minimums)
#     dI_maximums = dI_maximums[0] # np.asarray(dI_minimums)

#     dI_maximums_ok = []
#     for idx in U_minimums:
#         # расстояние от минимумов dI до текущего максимума dU
#         idx_maximums = dI_maximums - idx

#         idx_maximums[idx_maximums < 0] = 1000000

#         # Ближайший минимум dI после текущего максимума dU
#         i = np.min(idx_maximums)

#         dI_maximums_ok.append(i + idx)

#     spanlist = []
#     for i0, i1 in zip(U_minimums, dI_maximums_ok):
#         spanlist.append( (i0 + di_left, i1-di_right) )

#     if debug:
#         return spanlist, U_smooth, dI, dI*500
#     else:
#         return spanlist

def calc_Te(U, I, U_min, U_max, fit, span=None, details=False):
    """


    Parameters
    ----------
    U : 1D np.array
        Probe Voltage.
    I : 1D np.array
        Probe Current.
    U_min : float
        Minimal Voltage for diapason to calc.
    U_max : float
        Maximum Voltage for diapason to calc.
    fit : str
        'exp' - uses exponent to fit suit for case with negative I.
        'lin' - uses linear fit and semi log Current-Voltage plot.
    span : TYPE, optional
        DESCRIPTION. The default is None.
    details : bool, optional
        if True returns additional variables. The default is False.

    Returns
    -------
    1D np.array
        Te - electron temperature in eV.

    """

    if span is not None:
        i0, i1 = span
        U = U[i0:i1]
        I = I[i0:i1]

    # сохранение полного диапазона для ВАХ
    U_wide = U.copy()
    I_wide = I.copy()

    # отсечение отрицательных значений тока
    if fit == 'lin':
        mask = I > 0
        U = U[mask]
        I = I[mask]
        ln_I = np.log(I)

    # задание диапазона по напряжению
    mask = (U_min < U) & (U < U_max)
    if fit == 'lin':
        ln_I = ln_I[mask]
    U = U[mask]
    I = I[mask]

    if U.shape[0] == 0:
        Te = 0.0
        k, c, rvalue, pvalue, kerr, cerr = [0.0]*6
    else:
        if fit == 'lin':
            lin_res = linregress(U, ln_I)
            k, c = lin_res.slope, lin_res.intercept
            rvalue, pvalue = lin_res.rvalue, lin_res.pvalue
            kerr, cerr = lin_res.stderr, lin_res.intercept_stderr
            Te = 0.0 if np.isclose(k, 0) else 1.0/k
        elif fit == 'exp':
            popt, _ = curve_fit(exp_lp, np.asarray(U), np.asarray(I),
               (1.0, 1.0), maxfev=10**6, bounds=[(-10, -10), (10, 10)])
            k, c = popt
            Te = 0.0 if np.isclose(k, 0) else 1.0/k

    if details and fit == 'lin':
        return Te, (U, I, k, c, rvalue, pvalue, kerr, cerr, U_wide, I_wide)
    elif details and fit == 'exp':
        return Te, (U, I, k, c, U_wide, I_wide)
