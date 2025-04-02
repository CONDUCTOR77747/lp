# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 14:02:14 2025

@author: Ammosov, Eliseev

"""
import numpy as np
from scipy.stats import linregress
from scipy.optimize import curve_fit
from scipy.constants import physical_constants
from numpy.lib.stride_tricks import sliding_window_view
from ..processing import exp, remove_negatives
from  .span_detector import SpanDetector
#%% Default params
PROBE_AREA_DEFAULT = np.pi*(5)**2/4
M_I_DEFAULT = physical_constants['proton mass in u'][0]
#%%
class TeNeAnalyzer():
    """
    Calculates electron temperature on given spans.

    Parameters
    ----------
    t : ndarray
        1D array of time values in [ms].
    u : ndarray
        1D array of probe voltage in [V].
    i : ndarray
        1D array of probe current in [mA].

    Example:
        tna = TeNeAnalyzer(t, u, i, spans_te, spans_ne)
        te, info = tna.calc_te(n_avg, u_range, fit_method='linear')
        ne, info = tna.calc_ne()
    """
    def __init__(self, t, u, i):
        self.t, self.u, self.i = t, u, i
        self.spandet, self.spans_te, self.spans_ne = None, None, None


    def calc_te_ne(self, n_avg=1, dt_range_te=None, u_range=None,
                   sweep_direction='up', dt_range_ne=(2,2),
                   probe_area=PROBE_AREA_DEFAULT, m_i=M_I_DEFAULT,
                   fit_method='linear'):
        """ Calculate Te [eV] values for each Te span """

        self.spandet = SpanDetector(self.t, self.u, self.i)
        self.spans_te, self.spans_ne = self.spandet.spans(
            dt_range_te=dt_range_te,
            dt_range_ne=dt_range_ne,
            sweep_direction=sweep_direction
            )

        if n_avg <= 0:
            n_avg = 1

        spans_windowed = sliding_window_view(self.spans_te,
                                    window_shape=(n_avg, 2))

        res_t, res_te, res_ne, res_info = [], [], [], []
        for spans in spans_windowed:
            tt, uu, ii = np.array([]), np.array([]), np.array([])
            for span in spans[0]:
                i0, i1 = span
                tt = np.concatenate((tt, self.t[i0:i1]))
                uu = np.concatenate((uu, self.u[i0:i1]))
                ii = np.concatenate((ii, self.i[i0:i1]))

            # skip dot if nothing in it, helps avoid nans
            if len(tt) == 0 or len(uu) == 0 or len(ii) == 0:
                continue

            te, info = self.fit_data(uu, ii, u_range, fit_method=fit_method)
            if np.isclose(te, 0) or te <= 0:
                continue

            i_is = np.mean(ii)
            ne = self.ne_formula(te, i_is, probe_area, m_i)
            if ne <= 0:
                continue

            res_t.append(tt.mean())
            res_te.append(te)
            res_ne.append(ne)
            res_info.append(info)

        return (np.asarray(res_t), np.asarray(res_te), np.asarray(res_ne),
                np.asarray(res_info))

    def fit_data(self, u, i, u_range, fit_method='linear'):
        """ Filter data for fitting and use chosen method """
        fit_dict = {
            'linear': self.te_linear_fit,
            'exponential': self.te_exponential_fit
            }
        u_masked, i_masked = self.u_mask(u, i, u_range)
        te, info = fit_dict[fit_method](u_masked, i_masked)
        return te, info

    def te_linear_fit(self, u, i):
        """ fit Current-Voltage plot with scipy linregress """
        # remove negatives from current
        u, i = remove_negatives(u, i)
        # ln(I) for semilog Voltage-ln(Current) Plot
        ln_i = np.log(i)
        if len(u) == 0 or len(i) == 0:
            return 0, (0, 0, 0, 0)
        if np.any(np.isnan(u)) or np.any(np.isnan(ln_i)):
            raise ValueError("Входные данные содержат NaN!")

        lin_res = linregress(u, ln_i)
        k, c, kerr, cerr = (lin_res.slope, lin_res.intercept,
                            lin_res.stderr, lin_res.intercept_stderr)
        te = 0.0 if np.isclose(k, 0) else 1.0/k
        return te, (k, c, kerr, cerr)

    def te_exponential_fit(self, u, i):
        """ fit Current-Voltage plot with np.exp """
        if len(u) == 0:
            te, k, c, kerr, cerr = [0.0]*5
        else:
            popt, pcov = curve_fit(exp, u, i, (1.0, 1.0), maxfev=1e6,
                                bounds=[(-10, -10), (10, 10)])
            k, c = popt
            kerr, cerr = np.sqrt(np.diag(pcov))
            te = 0.0 if np.isclose(k, 0) else 1.0/k
        return te, (k, c, kerr, cerr)

    def u_mask(self, u, i, u_range):
        """ Mask voltage and current values by given voltage range """
        if u_range is None:
            return u, i

        mask = (u_range[0] < u) & (u < u_range[1])
        u = u[mask]
        i = i[mask]
        return u, i

    def ne_formula(self, te, i_is, probe_area, m_i):
        """ Calculate ne [10^(18) * m^(-3)] using formula """
        if (te is None or np.isnan(te) or np.isclose(probe_area, 0) or
            np.isclose(te, 0) or te <= 0):
            return 0.0
        return 1.12 * (i_is / probe_area) * np.sqrt(m_i / te)
