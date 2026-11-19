"""Beat-level data for the ML detector (Level 2): AAMI classes, segmentation, features."""

import numpy as np

# MIT-BIH beat symbols -> AAMI EC57 classes
AAMI_MAP = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q",
}
AAMI_CLASSES = ["N", "S", "V", "F", "Q"]


def segment_beats(signal, rpeaks, fs, before=0.25, after=0.45):
    """Cut a fixed window around each R peak. Returns (beats, kept_indices)."""
    b, a = int(before * fs), int(after * fs)
    beats, kept = [], []
    for i, r in enumerate(rpeaks):
        if r - b >= 0 and r + a <= len(signal):
            seg = signal[r - b:r + a]
            seg = (seg - seg.mean()) / (seg.std() + 1e-8)
            beats.append(seg)
            kept.append(i)
    return np.array(beats), np.array(kept, dtype=int)


def rr_features(rpeaks, fs):
    """Per-beat RR features: pre-RR, post-RR, local average RR, ratios.

    Index i of the output corresponds to rpeaks[i]; edges are padded.
    """
    rpeaks = np.asarray(rpeaks)
    rr = np.diff(rpeaks) / fs
    pre = np.concatenate([[rr[0]], rr])
    post = np.concatenate([rr, [rr[-1]]])
    local = np.convolve(pre, np.ones(10) / 10, mode="same")
    global_avg = np.full_like(pre, pre.mean())
    return np.column_stack([pre, post, local, pre / (local + 1e-8),
                            post / (pre + 1e-8), global_avg])


def morphology_features(beats, n_points=40):
    """Down-sampled beat waveform — a simple, explainable morphology descriptor."""
    idx = np.linspace(0, beats.shape[1] - 1, n_points).astype(int)
    return beats[:, idx]
