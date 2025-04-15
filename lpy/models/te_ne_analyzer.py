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
from ..processing import exp, remove_negatives, is_valid_positive, smooth
from  .span_detector import SpanDetector
#%% Default params
PROBE_AREA_DEFAULT = (np.pi*(5)**2) * np.sin(np.deg2rad(15)) / 4
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

    def calc_te_ne(self, parameters={}):
        """
        Calculate Te [eV] values for each Te span

        Parameters
        ----------
        parameters : dict, optional
            Dictionary containing tweak parameters for processing.
            The default is {}.

        Available keys
        --------------
        u_range : tuple(float, float), Default: (0,0)
            Sets min and max value to Voltage used in calculation.
        n_avg : int, Default: 1
            Window size corresponds to amount of scans to take into account.
        te_threshold : float, Default: 0
            Sets Te values to zero if above threshold value.
        sweep_direction : str, Default: 'up'
            Current sweep direction for evaluating Te. 'up' or 'down'.
        probe_area : float, Default: PROBE_AREA_DEFAULT
            Probe area in [mm^2].
        m_i : float, Default: M_I_DEFAULT
            Ion mass in [a.e.m.].
        smooth_u : tuple(int, int), Default: (1,1)
            Smooth input Voltage.
        smooth_i : tuple(int, int), Default: (1,1)
            Smooth input Current.
        dt_range_ne : tuple(float, float), Default: (2,2)
            Adjust ne spans boundaries by time in [ms].
        dt_range_te : tuple(float, float), Default: (0,0)
            Adjust Te spans boundaries by time in [ms].
        fit_method : str, Default: 'linear'
            Fit method using in calculating Te. 'linear' or 'exponential'.
        Returns
        -------
        (res_t, res_te, res_ne, res_info) : tuple(np.array,...)
            time, Te, ne, info (contains fit parameters k, c, kerr, cerr).
        """
        # setup parameters and defaults
        u_range = parameters.get('u_range', (0,0))
        n_avg = parameters.get('n_avg', 1)
        te_threshold = parameters.get('te_threshold', 0)
        sweep_direction = parameters.get('sweep_direction', 'up')
        probe_area = parameters.get('probe_area', PROBE_AREA_DEFAULT)
        m_i = parameters.get('m_i', M_I_DEFAULT)
        smooth_u = parameters.get('smooth_u', (1,1))
        smooth_i = parameters.get('smooth_i', (1,1))
        dt_range_ne = parameters.get('dt_range_ne', (2,2))
        dt_range_te = parameters.get('dt_range_te', (0,0))
        fit_method = parameters.get('fit_method', 'linear')

        # calculate spans for Te and ne
        self._calc_spans(dt_range_te=dt_range_te,
                        sweep_direction=sweep_direction,
                        dt_range_ne=dt_range_ne)

        # smooth U and I if needed
        self.u = smooth(self.u, *smooth_u)
        self.i = smooth(self.i, *smooth_i)

        # check window size positive or set 1
        if not is_valid_positive(n_avg):
            n_avg = 1
        spans_windowed_te = sliding_window_view(self.spans_te,
                                    window_shape=(int(n_avg), 2))
        spans_windowed_ne = sliding_window_view(self.spans_ne,
                                    window_shape=(int(n_avg), 2))

        # Current-Voltage Plot data list: u_wide, i_wide, u, i, k, c, time_mean
        cv_plot_data = []
        res_t, res_te, res_ne, res_info = [], [], [], [] # result lists
        for spans_te, spans_ne in zip(spans_windowed_te, spans_windowed_ne):
            tt, uu, ii, ii_ne = np.array([]), np.array([]), np.array([]), np.array([])
            for span_te, span_ne in zip(spans_te[0], spans_ne[0]):
                i0, i1 = span_te
                j0, j1 = span_ne
                tt = np.concatenate((tt, self.t[i0:i1]))
                uu = np.concatenate((uu, self.u[i0:i1]))
                ii = np.concatenate((ii, self.i[i0:i1]))
                ii_ne = np.concatenate((ii_ne, self.i[j0:j1]))

            # if nothing in spans add zeros to results
            if len(tt) == 0 or len(uu) == 0 or len(ii) == 0:
                # add zeros to results
                res = [0, 0, 0, 0]
                self._add_results(res_t, res_te, res_ne, res_info, res)
                cv_plot_data.append(([], [], [], [], 0, 0))
                continue

            te, info = self._fit_data(uu, ii, u_range, fit_method=fit_method)
            time_mean = tt.mean()
            # for Current-Voltage Plot
            u_m, i_m = self._u_mask(uu, ii, u_range) # masked by u_range
            # u_wide, i_wide, u, i, k, c, time_mean
            cv_plot_data.append((uu, ii, u_m, i_m, info[0], info[1], time_mean))

            # mean value of currents
            i_is = np.mean(ii_ne)
            ne = self._ne_formula(te, i_is, probe_area, m_i)

            res = [time_mean, te, ne, info]
            self._add_results(res_t, res_te, res_ne, res_info, res=res)

        res_t = np.array(res_t)
        res_te = np.array(res_te)
        res_ne = np.array(res_ne)
        res_info = np.array(res_info)

        # set peaks (by threshold) to zero if needed
        if te_threshold:
            mask = res_te > te_threshold
            res_te[mask] = 0.0
            res_ne[mask] = 0.0
            res_info[mask] = 0.0

        self.cv_plot_data = cv_plot_data # save data for Current-Voltage Plot
        return (res_t, res_te, res_ne, res_info)

    def _calc_spans(self, dt_range_te=None, sweep_direction='up',
                   dt_range_ne=(2,2)):
        """ Calculate spans for te and ne using SpanDetector """
        self.spandet = SpanDetector(self.t, self.u, self.i)
        self.spans_te, self.spans_ne = self.spandet.spans(
            dt_range_te=dt_range_te,
            dt_range_ne=dt_range_ne,
            sweep_direction=sweep_direction
            )

    def _add_results(self, res_t, res_te, res_ne, res_info, res):
        """
        Append results to data lists
        if no results return zeros
        """
        res_t.append(res[0])
        res_te.append(res[1])
        res_ne.append(res[2])
        res_info.append(res[3])

    def _fit_data(self, u, i, u_range, fit_method='linear'):
        """ Filter data for fitting and use chosen method """
        fit_dict = {
            'linear': self._te_linear_fit,
            'exponential': self._te_exponential_fit
            }
        u_masked, i_masked = self._u_mask(u, i, u_range)
        # self.u_i_masked.append((u_masked, i_masked)) # for Current-Voltage Plot
        te, info = fit_dict[fit_method](u_masked, i_masked)
        return te, info

    def _te_linear_fit(self, u, i):
        """ fit Current-Voltage plot with scipy linregress """
        # remove negatives from current
        u, i = remove_negatives(u, i)
        # ln(I) for semilog Voltage-ln(Current) Plot
        ln_i = np.log(i)

        if len(u) <= 1 or len(i) <= 1:
            return 0, (0, 0, 0, 0)

        if np.any(np.isnan(u)) or np.any(np.isnan(ln_i)):
            raise ValueError("Входные данные содержат NaN!")

        lin_res = linregress(u, ln_i)
        k, c, kerr, cerr = (lin_res.slope, lin_res.intercept,
                            lin_res.stderr, lin_res.intercept_stderr)

        if not is_valid_positive(k):
            return 0, (0, 0, 0, 0)

        return 1.0/k, (k, c, kerr, cerr)

    def _te_exponential_fit(self, u, i):
        """ fit Current-Voltage plot with np.exp """
        if len(u) <= 1 or len(i) <= 1:
            return 0, (0, 0, 0, 0)

        popt, pcov = curve_fit(exp, u, i, (1.0, 1.0), maxfev=1e6,
                            bounds=[(-10, -10), (10, 10)])
        k, c = popt
        kerr, cerr = np.sqrt(np.diag(pcov))

        if not is_valid_positive(k):
            return 0, (0, 0, 0, 0)

        return 1.0/k, (k, c, kerr, cerr)

    def _u_mask(self, u, i, u_range):
        """ Mask voltage and current values by given voltage range """
        if u_range is None or u_range[0] == 0 and u_range[1] == 0:
            return u, i

        mask = (u_range[0] < u) & (u < u_range[1])
        u = u[mask]
        i = i[mask]
        return u, i

    def _ne_formula(self, te, i_is, probe_area, m_i):
        """ Calculate ne [10^(18) * m^(-3)] using formula """
        # check te and probe_area positive values
        if not is_valid_positive(te) or not is_valid_positive(probe_area):
            return 0.0

        ne = 1.12 * (i_is / probe_area) * np.sqrt(m_i / te)

        if not is_valid_positive(ne):
            return 0.0

        return ne

    def find_nearest_info(self, t):
        """ find nearest span in spans_te by time value """
        if t is None:
            return
        span_times = [self.t[span[0]:span[1]].mean() for span in self.spans_te]
        dt = np.abs(span_times - t)
        i = np.nanargmin(dt)
        return i
