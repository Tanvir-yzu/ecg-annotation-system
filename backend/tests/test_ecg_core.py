"""Tests for ecg_core on synthetic ECG (no dataset download needed).

Run from backend/:  python -m pytest tests -q   (or: python tests/test_ecg_core.py)
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ecg_core import (preprocess, detect_rpeaks, evaluate_rpeaks,  # noqa: E402
                      detect_rhythm_events, heart_rate_series)
from ecg_core.beats import segment_beats, rr_features  # noqa: E402

FS = 360


def synthetic_ecg(rr_seconds, fs=FS, noise=0.05, seed=0):
    """Sum-of-Gaussians PQRST beats placed at the given RR intervals."""
    rng = np.random.default_rng(seed)
    r_times = np.cumsum(np.concatenate([[1.0], rr_seconds]))
    n = int((r_times[-1] + 1.0) * fs)
    t = np.arange(n) / fs
    x = np.zeros(n)
    waves = [(-0.20, 0.10, 0.025),  # P
             (-0.03, -0.10, 0.008),  # Q
             (0.00, 1.20, 0.010),    # R
             (0.03, -0.25, 0.008),   # S
             (0.25, 0.30, 0.040)]    # T
    for rt in r_times:
        for off, amp, width in waves:
            x += amp * np.exp(-((t - rt - off) ** 2) / (2 * width ** 2))
    x += 0.3 * np.sin(2 * np.pi * 0.2 * t)          # baseline wander
    x += noise * rng.standard_normal(n)              # noise
    return x, (r_times * fs).astype(int)


def test_rpeak_detection_normal_rhythm():
    x, ref = synthetic_ecg(np.full(60, 0.8))          # 75 bpm
    det = detect_rpeaks(preprocess(x, FS), FS)
    m = evaluate_rpeaks(det, ref, FS)
    assert m["Se"] > 0.98 and m["PPV"] > 0.98, m


def test_tachycardia_detected():
    x, _ = synthetic_ecg(np.full(40, 0.5))           # 120 bpm
    det = detect_rpeaks(preprocess(x, FS), FS)
    labels = {e.label for e in detect_rhythm_events(det, FS)}
    assert "Tachycardia" in labels


def test_bradycardia_detected():
    x, _ = synthetic_ecg(np.full(30, 1.25))          # 48 bpm
    det = detect_rpeaks(preprocess(x, FS), FS)
    labels = {e.label for e in detect_rhythm_events(det, FS)}
    assert "Bradycardia" in labels


def test_normal_rhythm_has_no_events():
    x, _ = synthetic_ecg(np.full(40, 0.8))
    det = detect_rpeaks(preprocess(x, FS), FS)
    assert detect_rhythm_events(det, FS) == []


def test_irregular_and_pause_detected():
    rng = np.random.default_rng(1)
    rr = rng.uniform(0.45, 1.1, 40)
    rr[20] = 2.6                                      # a pause
    x, _ = synthetic_ecg(rr)
    det = detect_rpeaks(preprocess(x, FS), FS)
    labels = {e.label for e in detect_rhythm_events(det, FS)}
    assert {"Irregular", "Pause"} <= labels, labels


def test_heart_rate_and_features():
    x, ref = synthetic_ecg(np.full(20, 0.75))
    _, hr = heart_rate_series(ref, FS)
    assert np.allclose(hr, 80, atol=1)
    beats, kept = segment_beats(preprocess(x, FS), ref, FS)
    assert beats.shape[1] == int(0.25 * FS) + int(0.45 * FS)
    assert rr_features(ref, FS).shape == (len(ref), 6)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
