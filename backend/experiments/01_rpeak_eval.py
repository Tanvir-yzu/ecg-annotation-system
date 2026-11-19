"""Experiment 1 — R-peak detection accuracy on all 48 MIT-BIH records.

Output: results/01_rpeak_eval.csv + overall Se / PPV / F1 (thesis table, CV number).
"""

import numpy as np
import pandas as pd

from common import DATA_DIR, RESULTS_DIR, ensure_mitbih, record_ids
from ecg_core import detect_rpeaks, evaluate_rpeaks, preprocess
from ecg_core.beats import AAMI_MAP
from ecg_core.io import load_record


def main():
    ensure_mitbih()
    rows = []
    for rid in record_ids():
        rec = load_record(DATA_DIR / str(rid))
        fs = rec["fs"]
        # reference = annotated heartbeats only (skip rhythm / noise markers)
        ref = np.array([s for s, sym in zip(rec["beat_samples"], rec["beat_symbols"]) if sym in AAMI_MAP])
        det = detect_rpeaks(preprocess(rec["signal"], fs), fs)
        m = evaluate_rpeaks(det, ref, fs)
        rows.append({"record": rid, **m})
        print(f"{rid}: Se={m['Se']:.4f} PPV={m['PPV']:.4f}")

    df = pd.DataFrame(rows)
    tp, fp, fn = df.TP.sum(), df.FP.sum(), df.FN.sum()
    se, ppv = tp / (tp + fn), tp / (tp + fp)
    total = {"record": "TOTAL", "TP": tp, "FP": fp, "FN": fn, "Se": se, "PPV": ppv,
             "F1": 2 * se * ppv / (se + ppv)}
    df = pd.concat([df, pd.DataFrame([total])], ignore_index=True)
    df.to_csv(RESULTS_DIR / "01_rpeak_eval.csv", index=False)
    print(f"\nOVERALL  beats={tp + fn}  Se={se:.4f}  PPV={ppv:.4f}  F1={total['F1']:.4f}")


if __name__ == "__main__":
    main()
