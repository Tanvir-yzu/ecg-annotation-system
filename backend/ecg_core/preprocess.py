"""Signal preprocessing: band-pass filtering and baseline-wander removal."""

import numpy as np
from scipy.signal import butter, filtfilt, medfilt


def bandpass_filter(signal, fs, low=0.5, high=40.0, order=3):
    """Zero-phase Butterworth band-pass filter.

    0.5 Hz removes baseline wander; 40 Hz removes muscle noise and
    50/60 Hz power-line interference while keeping the QRS complex.
    """
    signal = np.asarray(signal, dtype=float)
    nyq = fs / 2.0
    high = min(high, nyq * 0.99)
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, signal)


def remove_baseline(signal, fs):
    """Baseline removal with two cascaded median filters (200 ms, 600 ms).

    A classic alternative to high-pass filtering that distorts the
    ST segment less. Useful as a comparison in the thesis.
    """
    signal = np.asarray(signal, dtype=float)
    w1 = int(0.2 * fs) | 1  # odd window length
    w2 = int(0.6 * fs) | 1
    baseline = medfilt(medfilt(signal, w1), w2)
    return signal - baseline


def preprocess(signal, fs):
    """Default pipeline used by the system."""
    return bandpass_filter(signal, fs)
