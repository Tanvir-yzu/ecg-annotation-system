"""Experiment 3 — AAMI beat classification, INTER-PATIENT (DS1 train -> DS2 test).

Compares models on the same features so the thesis has a fair baseline table:
  - Random Forest   on RR features
  - Random Forest   on RR + morphology features
  - Logistic Regression on RR + morphology features

Uses reference R-peak locations (standard practice for classifier evaluation).
Output: results/03_beat_classifier.csv, confusion matrices, saved best model.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import DATA_DIR, RESULTS_DIR, ensure_mitbih
from ecg_core import preprocess
from ecg_core.beats import AAMI_CLASSES, AAMI_MAP, morphology_features, rr_features, segment_beats
from ecg_core.io import load_record
from ecg_core.splits import DS1_TRAIN, DS2_TEST


def build_features(signal, beat_samples, beat_symbols, fs):
    """Return (X_rr, X_morph, y) for the beats of one record."""
    keep = [i for i, s in enumerate(beat_symbols) if s in AAMI_MAP]
    r = np.asarray(beat_samples)[keep]
    y = np.array([AAMI_MAP[beat_symbols[i]] for i in keep])
    x = preprocess(signal, fs)
    beats, kept = segment_beats(x, r, fs)
    rr = rr_features(r, fs)[kept]
    return rr, morphology_features(beats), y[kept]


def load_split(ids):
    RR, MO, Y = [], [], []
    for rid in ids:
        rec = load_record(DATA_DIR / str(rid))
        rr, mo, y = build_features(rec["signal"], rec["beat_samples"], rec["beat_symbols"], rec["fs"])
        RR.append(rr), MO.append(mo), Y.append(y)
    return np.vstack(RR), np.vstack(MO), np.concatenate(Y)


def models():
    return {
        "RF_rr": (lambda rr, mo: rr,
                  RandomForestClassifier(300, class_weight="balanced", n_jobs=-1, random_state=0)),
        "RF_rr+morph": (lambda rr, mo: np.hstack([rr, mo]),
                        RandomForestClassifier(300, class_weight="balanced", n_jobs=-1, random_state=0)),
        "LogReg_rr+morph": (lambda rr, mo: np.hstack([rr, mo]),
                            make_pipeline(StandardScaler(),
                                          LogisticRegression(max_iter=2000, class_weight="balanced"))),
    }


def evaluate(name, y_true, y_pred):
    labels = [c for c in AAMI_CLASSES if c in set(y_true)]
    rep = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    row = {"model": name, "accuracy": rep["accuracy"],
           "macro_F1": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)}
    for c in labels:
        row[f"{c}_Se"] = rep[c]["recall"]
        row[f"{c}_PPV"] = rep[c]["precision"]
    cm = pd.DataFrame(confusion_matrix(y_true, y_pred, labels=labels), index=labels, columns=labels)
    return row, cm


def main():
    ensure_mitbih()
    print("Loading DS1 (train) ...")
    rr_tr, mo_tr, y_tr = load_split(DS1_TRAIN)
    print("Loading DS2 (test) ...")
    rr_te, mo_te, y_te = load_split(DS2_TEST)
    print("Train class counts:", pd.Series(y_tr).value_counts().to_dict())
    print("Test  class counts:", pd.Series(y_te).value_counts().to_dict())

    rows, best = [], (None, -1)
    for name, (feat, clf) in models().items():
        clf.fit(feat(rr_tr, mo_tr), y_tr)
        pred = clf.predict(feat(rr_te, mo_te))
        row, cm = evaluate(name, y_te, pred)
        rows.append(row)
        cm.to_csv(RESULTS_DIR / f"03_confusion_{name}.csv")
        print(f"\n{name}: acc={row['accuracy']:.4f} macro-F1={row['macro_F1']:.4f}\n{cm}")
        if row["macro_F1"] > best[1]:
            best = (name, row["macro_F1"])
            joblib.dump(clf, RESULTS_DIR / "best_beat_model.joblib")

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "03_beat_classifier.csv", index=False)
    print(f"\nBest model: {best[0]} (macro-F1 {best[1]:.4f}) -> results/best_beat_model.joblib")


if __name__ == "__main__":
    main()
