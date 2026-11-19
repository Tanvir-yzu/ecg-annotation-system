"""Loading ECG records (WFDB format: MIT-BIH, PTB-XL)."""

from pathlib import Path

import numpy as np


def load_record(path, channel=0):
    """Load a WFDB record.

    path: record path WITHOUT extension, e.g. 'data/mitdb/100'.
    Returns dict(signal, fs, leads, n_samples, beat_samples, beat_symbols).
    beat_* are empty if the record has no .atr annotation file.
    """
    import wfdb  # imported lazily so the rest of ecg_core works without it

    rec = wfdb.rdrecord(str(path))
    out = {
        "signal": rec.p_signal[:, channel].astype(float),
        "all_signals": rec.p_signal.astype(float),
        "fs": float(rec.fs),
        "leads": list(rec.sig_name),
        "n_samples": int(rec.sig_len),
        "beat_samples": np.array([], dtype=int),
        "beat_symbols": [],
    }
    if Path(str(path) + ".atr").exists():
        ann = wfdb.rdann(str(path), "atr")
        out["beat_samples"] = np.asarray(ann.sample, dtype=int)
        out["beat_symbols"] = list(ann.symbol)
    return out


def download_mitbih(target_dir="data/mitdb"):
    """Download MIT-BIH Arrhythmia Database from PhysioNet (~100 MB)."""
    import wfdb

    Path(target_dir).mkdir(parents=True, exist_ok=True)
    wfdb.dl_database("mitdb", dl_dir=str(target_dir))
