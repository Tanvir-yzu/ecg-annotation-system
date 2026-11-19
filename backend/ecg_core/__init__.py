"""ecg_core — framework-free ECG signal processing and detection.

Used by both the Django web system and the offline thesis experiments,
so every result in the thesis comes from the same code the system runs.
"""

from .preprocess import bandpass_filter, remove_baseline, preprocess
from .rpeaks import detect_rpeaks, evaluate_rpeaks
from .rhythm import heart_rate_series, detect_rhythm_events, RhythmEvent

__all__ = [
    "bandpass_filter",
    "remove_baseline",
    "preprocess",
    "detect_rpeaks",
    "evaluate_rpeaks",
    "heart_rate_series",
    "detect_rhythm_events",
    "RhythmEvent",
]
