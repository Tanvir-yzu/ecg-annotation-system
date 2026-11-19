"""Experiment 2 — rule-based rhythm detection on one record, with a figure.

Usage:  python experiments/02_rhythm_rules.py 203
Output: results/02_rhythm_<record>.png and printed events.
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import DATA_DIR, RESULTS_DIR, ensure_mitbih
from ecg_core import detect_rhythm_events, detect_rpeaks, heart_rate_series, preprocess
from ecg_core.io import load_record

COLORS = {"Tachycardia": "tab:red", "Bradycardia": "tab:blue", "Irregular": "tab:orange", "Pause": "tab:purple"}


def main(rid="203"):
    ensure_mitbih()
    rec = load_record(DATA_DIR / rid)
    fs = rec["fs"]
    x = preprocess(rec["signal"], fs)
    r = detect_rpeaks(x, fs)
    events = detect_rhythm_events(r, fs)

    print(f"Record {rid}: {len(r)} beats, {len(events)} events")
    for e in events[:30]:
        print(f"  {e.label:12s} {e.start / fs:8.1f}s - {e.end / fs:8.1f}s  {e.detail}")

    t_hr, hr = heart_rate_series(r, fs)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    a1.plot(t_hr / fs, hr, lw=0.8, color="black")
    a1.axhline(100, ls="--", c="tab:red", lw=0.8)
    a1.axhline(60, ls="--", c="tab:blue", lw=0.8)
    a1.set_ylabel("Heart rate (bpm)")
    for e in events:
        a1.axvspan(e.start / fs, e.end / fs, color=COLORS.get(e.label, "grey"), alpha=0.2)

    w = slice(0, int(20 * fs))
    a2.plot(np.arange(len(x))[w] / fs, x[w], lw=0.7)
    a2.plot(r[r < w.stop] / fs, x[r[r < w.stop]], "rx")
    a2.set_xlabel("Time (s)")
    a2.set_ylabel("ECG (mV), first 20 s")
    fig.suptitle(f"MIT-BIH {rid}: rule-based rhythm events")
    fig.tight_layout()
    out = RESULTS_DIR / f"02_rhythm_{rid}.png"
    fig.savefig(out, dpi=150)
    print("Saved", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "203")
