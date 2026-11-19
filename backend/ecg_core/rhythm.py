"""Rule-based abnormal rhythm detection from RR intervals (Level 1 detector).

Rules (adult resting ECG, thresholds configurable):
  - Tachycardia : mean HR in window > 100 bpm
  - Bradycardia : mean HR in window < 60 bpm
  - Irregular   : RR coefficient of variation in window > 0.15
  - Pause       : a single RR interval > 2.0 s
"""

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class RhythmEvent:
    start: int  # sample index
    end: int    # sample index
    label: str
    confidence: float
    detail: str = ""

    def to_dict(self):
        return asdict(self)


DEFAULT_RULES = {
    "tachy_bpm": 100.0,
    "brady_bpm": 60.0,
    "irregular_cv": 0.15,
    "pause_s": 2.0,
    "window_beats": 8,
}


def heart_rate_series(rpeaks, fs):
    """Instantaneous heart rate (bpm) at each beat after the first."""
    rpeaks = np.asarray(rpeaks)
    if len(rpeaks) < 2:
        return np.array([]), np.array([])
    rr = np.diff(rpeaks) / fs
    return rpeaks[1:], 60.0 / rr


def _merge(events):
    """Merge overlapping or touching events that share a label."""
    events = sorted(events, key=lambda e: (e.label, e.start))
    merged = []
    for e in events:
        if merged and merged[-1].label == e.label and e.start <= merged[-1].end:
            m = merged[-1]
            m.end = max(m.end, e.end)
            m.confidence = max(m.confidence, e.confidence)
        else:
            merged.append(e)
    return sorted(merged, key=lambda e: e.start)


def detect_rhythm_events(rpeaks, fs, rules=None):
    """Slide a window of N beats over the record and flag abnormal rhythm."""
    r = {**DEFAULT_RULES, **(rules or {})}
    rpeaks = np.asarray(rpeaks)
    events = []
    if len(rpeaks) < 3:
        return events

    rr = np.diff(rpeaks) / fs

    # pauses: single long RR
    for i, v in enumerate(rr):
        if v > r["pause_s"]:
            events.append(RhythmEvent(int(rpeaks[i]), int(rpeaks[i + 1]), "Pause",
                                      min(1.0, v / (2 * r["pause_s"])), f"RR={v:.2f}s"))

    n = int(r["window_beats"])
    for i in range(0, max(1, len(rr) - n + 1)):
        w = rr[i:i + n]
        if len(w) < 3:
            continue
        hr = 60.0 / w.mean()
        cv = w.std() / w.mean()
        start, end = int(rpeaks[i]), int(rpeaks[min(i + n, len(rpeaks) - 1)])
        if hr > r["tachy_bpm"]:
            events.append(RhythmEvent(start, end, "Tachycardia",
                                      min(1.0, (hr - r["tachy_bpm"]) / 50 + 0.5), f"HR={hr:.0f}"))
        elif hr < r["brady_bpm"]:
            events.append(RhythmEvent(start, end, "Bradycardia",
                                      min(1.0, (r["brady_bpm"] - hr) / 30 + 0.5), f"HR={hr:.0f}"))
        if cv > r["irregular_cv"]:
            events.append(RhythmEvent(start, end, "Irregular",
                                      min(1.0, cv / (2 * r["irregular_cv"])), f"CV={cv:.2f}"))
    return _merge(events)
