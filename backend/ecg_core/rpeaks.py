"""R-peak detection (Pan-Tompkins style) and evaluation against reference beats."""

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def detect_rpeaks(signal, fs, refractory=0.25):
    """Detect R peaks.

    Steps (after Pan & Tompkins, 1985):
      1. band-pass 5-15 Hz to emphasise the QRS complex
      2. derivative -> squaring -> 150 ms moving-window integration
      3. adaptive threshold on the integrated signal
      4. refine each detection to the largest |amplitude| in the raw signal

    Returns sample indices of R peaks.
    """
    x = np.asarray(signal, dtype=float)
    nyq = fs / 2.0
    b, a = butter(2, [5 / nyq, 15 / nyq], btype="band")
    y = filtfilt(b, a, x)

    d = np.gradient(y)
    sq = d ** 2
    win = max(1, int(0.15 * fs))
    integ = np.convolve(sq, np.ones(win) / win, mode="same")

    # adaptive threshold: fraction of a robust high percentile, per 10 s block
    thr = np.zeros_like(integ)
    block = int(10 * fs)
    for start in range(0, len(integ), block):
        seg = integ[start:start + block]
        thr[start:start + block] = 0.3 * np.percentile(seg, 98)

    peaks, _ = find_peaks(integ, height=thr, distance=int(refractory * fs))

    # refine to the true R location in the band-passed signal (±75 ms)
    search = int(0.075 * fs)
    refined = []
    for p in peaks:
        lo, hi = max(0, p - search), min(len(y), p + search)
        refined.append(lo + int(np.argmax(np.abs(y[lo:hi]))))
    refined = np.unique(refined)

    # drop duplicates closer than the refractory period
    if len(refined) > 1:
        keep = [refined[0]]
        for r in refined[1:]:
            if r - keep[-1] >= int(refractory * fs):
                keep.append(r)
        refined = np.array(keep)
    return np.asarray(refined, dtype=int)


def evaluate_rpeaks(detected, reference, fs, tolerance=0.15):
    """Match detections to reference beats within ±tolerance seconds.

    Returns a dict with TP, FP, FN, sensitivity (Se), positive predictive
    value (PPV) and F1 — the standard metrics for QRS detectors.
    """
    detected = np.sort(np.asarray(detected))
    reference = np.sort(np.asarray(reference))
    tol = int(tolerance * fs)

    used = np.zeros(len(detected), dtype=bool)
    tp = 0
    for r in reference:
        idx = np.searchsorted(detected, r)
        best, best_dist = None, tol + 1
        for j in (idx - 1, idx):
            if 0 <= j < len(detected) and not used[j]:
                dist = abs(detected[j] - r)
                if dist < best_dist:
                    best, best_dist = j, dist
        if best is not None and best_dist <= tol:
            used[best] = True
            tp += 1

    fn = len(reference) - tp
    fp = len(detected) - tp
    se = tp / (tp + fn) if tp + fn else 0.0
    ppv = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * se * ppv / (se + ppv) if se + ppv else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "Se": se, "PPV": ppv, "F1": f1}
