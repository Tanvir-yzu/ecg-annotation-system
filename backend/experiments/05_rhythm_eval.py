"""Experiment 5 — evaluate the rule-based rhythm detector against MIT-BIH reference rhythm labels.

Each record is cut into 10 s windows. A window's TRUE label comes from the
reference rhythm annotation covering most of it; its PREDICTED labels are the
detector events that overlap it.

Reports per class: Se, PPV, and false alarms per hour on Normal-rhythm windows.
Run it before and after changing rules (ecg_core/rhythm.py DEFAULT_RULES) to
show the improvement in the thesis.

Usage:  python experiments/05_rhythm_eval.py
        python experiments/05_rhythm_eval.py --brady 50 --cv 0.20 --window-beats 12
"""

import argparse

import numpy as np
import pandas as pd

from common import DATA_DIR, RESULTS_DIR, ensure_mitbih, record_ids
from ecg_core import detect_rhythm_events, detect_rpeaks, preprocess
from ecg_core.io import load_record

# reference rhythm code -> evaluated class
REF_MAP = {"(N": "Normal", "(SBR": "Bradycardia", "(SVTA": "Tachycardia", "(VT": "Tachycardia",
           "(AFIB": "Irregular", "(AFL": "Irregular"}
CLASSES = ["Tachycardia", "Bradycardia", "Irregular"]
WIN_S = 10


def reference_segments(path, n_samples):
    import wfdb
    ann = wfdb.rdann(str(path), "atr")
    marks = [(int(s), a.strip("\x00")) for s, a in zip(ann.sample, ann.aux_note) if a.strip("\x00").startswith("(")]
    segs = []
    for i, (start, code) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else n_samples
        segs.append((start, end, REF_MAP.get(code, "Other")))
    return segs


def window_truth(segs, a, b):
    """Reference class covering most of window [a, b)."""
    cover = {}
    for s, e, lab in segs:
        ov = min(b, e) - max(a, s)
        if ov > 0:
            cover[lab] = cover.get(lab, 0) + ov
    return max(cover, key=cover.get) if cover else "Other"


def evaluate_record(signal, fs, segs, rules):
    r = detect_rpeaks(preprocess(signal, fs), fs)
    events = detect_rhythm_events(r, fs, rules)
    w = int(WIN_S * fs)
    rows = []
    for a in range(0, len(signal) - w + 1, w):
        b = a + w
        truth = window_truth(segs, a, b)
        pred = {e.label for e in events if e.end > a and e.start < b}
        rows.append({"truth": truth, **{c: c in pred for c in CLASSES}})
    return rows


def summarise(df):
    out = []
    normal_hours = (df.truth == "Normal").sum() * WIN_S / 3600
    for c in CLASSES:
        pos = df.truth == c
        pred = df[c]
        tp = int((pos & pred).sum())
        fn = int((pos & ~pred).sum())
        fp = int((~pos & pred).sum())
        fa_normal = int(((df.truth == "Normal") & pred).sum())
        out.append({
            "class": c, "windows_true": int(pos.sum()), "TP": tp, "FN": fn, "FP": fp,
            "Se": tp / (tp + fn) if tp + fn else float("nan"),
            "PPV": tp / (tp + fp) if tp + fp else float("nan"),
            "false_alarms_per_hour_normal": fa_normal / normal_hours if normal_hours else float("nan"),
        })
    return pd.DataFrame(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tachy", type=float, default=None)
    p.add_argument("--brady", type=float, default=None)
    p.add_argument("--cv", type=float, default=None)
    p.add_argument("--window-beats", type=int, default=None)
    p.add_argument("--tag", default="default")
    args = p.parse_args()
    rules = {k: v for k, v in {"tachy_bpm": args.tachy, "brady_bpm": args.brady,
                                "irregular_cv": args.cv, "window_beats": args.window_beats}.items() if v is not None}

    ensure_mitbih()
    rows = []
    for rid in record_ids():
        rec = load_record(DATA_DIR / str(rid))
        segs = reference_segments(DATA_DIR / str(rid), rec["n_samples"])
        rows += evaluate_record(rec["signal"], rec["fs"], segs, rules)
        print(f"{rid} done")

    df = pd.DataFrame(rows)
    df = df[df.truth != "Other"]          # rhythms the rules do not target
    res = summarise(df)
    res.insert(0, "rules", args.tag + " " + str(rules or "defaults"))
    out = RESULTS_DIR / f"05_rhythm_eval_{args.tag}.csv"
    res.to_csv(out, index=False)
    print(f"\nWindows evaluated: {len(df)}  (Normal: {(df.truth == 'Normal').sum()})")
    print(res.drop(columns="rules").to_string(index=False, float_format="%.3f"))
    print("Saved", out)


if __name__ == "__main__":
    main()