# -*- coding: utf-8 -*-
"""
@author: Ammosov

lpy package init file
"""
from .load import load
from .models import SpanDetector, TeNeAnalyzer
from .plotting import create_interactive_plot
from .processing import (smooth, remove_peaks_iqr, remove_nans,
                         remove_negatives, remove_peaks_by_threshold, exp)
