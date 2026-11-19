"""Glue between Django and ecg_core: signal loading (cached) and detection runs."""

from functools import lru_cache

import numpy as np
from django.conf import settings
from django.db import transaction

from ecg_core import detect_rhythm_events, detect_rpeaks, preprocess
from ecg_core.io import load_record

from .models import Annotation


@lru_cache(maxsize=16)
def _load(file_path):
    rec = load_record(settings.ECG_DATA_DIR / file_path)
    return rec["all_signals"], rec["fs"]


@lru_cache(maxsize=16)
def _filtered(file_path, lead):
    signals, fs = _load(file_path)
    return preprocess(signals[:, lead], fs)


@lru_cache(maxsize=16)
def _rpeaks(file_path, lead):
    signals, fs = _load(file_path)
    return detect_rpeaks(_filtered(file_path, lead), fs)


def get_window(record, start, end, lead=0, filtered=True, max_points=None):
    """Return a (possibly down-sampled) window of signal plus R peaks inside it."""
    signals, fs = _load(record.file_path)
    n = signals.shape[0]
    start, end = max(0, int(start)), min(n, int(end))
    x = _filtered(record.file_path, lead) if filtered else signals[:, lead]
    seg = x[start:end]

    max_points = max_points or settings.ECG_MAX_POINTS
    step = max(1, int(np.ceil(len(seg) / max_points)))
    idx = np.arange(start, end, step)

    r = _rpeaks(record.file_path, lead)
    r = r[(r >= start) & (r < end)]
    return {
        "fs": fs, "start": start, "end": end, "step": step, "lead": lead,
        "samples": idx.tolist(),
        "values": np.round(x[idx], 4).tolist(),
        "rpeaks": r.tolist(),
    }


@transaction.atomic
def run_detection(record, lead=0, rules=None):
    """Run the rule-based detector and store its output as auto annotations.

    Unverified auto annotations from an earlier run are replaced; anything a
    person verified or made by hand is kept.
    """
    signals, fs = _load(record.file_path)
    r = _rpeaks(record.file_path, lead)
    events = detect_rhythm_events(r, fs, rules)

    record.annotations.filter(source=Annotation.Source.AUTO, verified=False).delete()
    created = Annotation.objects.bulk_create([
        Annotation(record=record, start_sample=e.start, end_sample=e.end, lead=lead,
                   label=e.label, source=Annotation.Source.AUTO,
                   confidence=round(e.confidence, 3), note=e.detail)
        for e in events
    ])
    rr = np.diff(r) / fs
    summary = {
        "beats": int(len(r)),
        "mean_hr": round(float(60 / rr.mean()), 1) if len(rr) else None,
        "events": len(created),
    }
    return created, summary
