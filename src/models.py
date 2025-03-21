import numpy as np
from processing import calc_spanlist, calc_Te

class TeData:
    def __init__(self, t, U, I, Ksmooth, dt_left, dt_right, U_min, U_max, fit):

        self.t, self.U, self.I = t, U, I

        self.spans, self.U_smooth, self.dI, self.sin_abs = calc_spanlist(t, U, I, Ksmooth, dt_left, dt_right, debug=True)

        self.Te_times = None
        self.Te = None
        self.info = None

        self.step = None
        self.n_avg = None

        self.U_min = U_min
        self.U_max = U_max

        self.fit = fit

    def avg_Te(self, step, n_avg):
        self.step = step
        self.n_avg = n_avg

        i = n_avg // 2
        d = n_avg // 2

        result_t = []
        result_Te = []
        result_info = []
        result_spans = []

        while True:
            if i+d+1 >= len(self.spans):
                break

            i0, i1 = self.spans[i-d]
            tt = self.t[i0:i1]
            xx = self.U[i0:i1]
            yy = self.I[i0:i1]

            for j in range(i-d+1, i+d+1):
                i0, i1 = self.spans[j]
                tt = np.hstack((tt, self.t[i0:i1]))
                xx = np.hstack((xx, self.U[i0:i1]))
                yy = np.hstack((yy, self.I[i0:i1]))

            Te, info = calc_Te(xx, yy, self.U_min, self.U_max, self.fit, details=True)

            # skip dot if nothing in it
            if len(tt) == 0 and len(xx) == 0 and len(yy) == 0:
                i += step
                continue

            result_t.append(tt.mean())
            # result_t.append(0.5*(tt[0] + tt[-1]))
            result_Te.append(Te)
            result_info.append((tt,) + info)
            result_spans.append(self.spans[i])

            i += step


        self.Te = result_Te
        self.Te_times = result_t
        self.Te_spans = result_spans
        self.info = result_info

        return np.asarray(result_t), np.asarray(result_Te), result_info

    def find_nearest_info(self, t):
        span_times = [self.t[span[0]:span[1]].mean() for span in self.Te_spans]
        dt = np.abs(span_times - t)
        i = np.nanargmin(dt)
        return i
