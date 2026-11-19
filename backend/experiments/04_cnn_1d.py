"""Experiment 4 — 1D-CNN beat classifier (PyTorch), same inter-patient split.

Input per beat: the raw beat window (252 samples at 360 Hz) + 6 RR features.
Requires:  pip install torch
Output: results/04_cnn_1d.csv, results/cnn_1d.pt
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from common import DATA_DIR, RESULTS_DIR, ensure_mitbih
from ecg_core import preprocess
from ecg_core.beats import AAMI_CLASSES, AAMI_MAP, rr_features, segment_beats
from ecg_core.io import load_record
from ecg_core.splits import DS1_TRAIN, DS2_TEST

import importlib
evaluate = importlib.import_module("03_beat_classifier").evaluate

CLS = {c: i for i, c in enumerate(AAMI_CLASSES)}


def load_split(ids):
    B, R, Y = [], [], []
    for rid in ids:
        rec = load_record(DATA_DIR / str(rid))
        keep = [i for i, s in enumerate(rec["beat_symbols"]) if s in AAMI_MAP]
        r = rec["beat_samples"][keep]
        y = np.array([CLS[AAMI_MAP[rec["beat_symbols"][i]]] for i in keep])
        beats, kept = segment_beats(preprocess(rec["signal"], rec["fs"]), r, rec["fs"])
        B.append(beats), R.append(rr_features(r, rec["fs"])[kept]), Y.append(y[kept])
    return np.vstack(B).astype("float32"), np.vstack(R).astype("float32"), np.concatenate(Y)


class BeatCNN(nn.Module):
    def __init__(self, n_rr=6, n_classes=5):
        super().__init__()
        def block(i, o, k):
            return nn.Sequential(nn.Conv1d(i, o, k, padding=k // 2), nn.BatchNorm1d(o), nn.ReLU(), nn.MaxPool1d(2))
        self.conv = nn.Sequential(block(1, 16, 7), block(16, 32, 5), block(32, 64, 3),
                                  nn.AdaptiveAvgPool1d(8), nn.Flatten())
        self.head = nn.Sequential(nn.Linear(64 * 8 + n_rr, 64), nn.ReLU(), nn.Dropout(0.3),
                                  nn.Linear(64, n_classes))

    def forward(self, beat, rr):
        return self.head(torch.cat([self.conv(beat.unsqueeze(1)), rr], dim=1))


def main(epochs=15, batch=256):
    ensure_mitbih()
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    btr, rtr, ytr = load_split(DS1_TRAIN)
    bte, rte, yte = load_split(DS2_TEST)
    mu, sd = rtr.mean(0), rtr.std(0) + 1e-8
    rtr, rte = (rtr - mu) / sd, (rte - mu) / sd

    counts = np.bincount(ytr, minlength=len(AAMI_CLASSES)).astype("float32")
    weights = torch.tensor(np.where(counts > 0, counts.sum() / (len(counts) * np.maximum(counts, 1)), 0.0))
    model = BeatCNN().to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss(weight=weights.to(dev))
    dl = DataLoader(TensorDataset(torch.tensor(btr), torch.tensor(rtr), torch.tensor(ytr)),
                    batch_size=batch, shuffle=True)

    for ep in range(epochs):
        model.train()
        total = 0.0
        for b, r, y in dl:
            b, r, y = b.to(dev), r.to(dev), y.to(dev)
            opt.zero_grad()
            loss = loss_fn(model(b, r), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(y)
        print(f"epoch {ep + 1}/{epochs} loss={total / len(ytr):.4f}")

    model.eval()
    with torch.no_grad():
        pred = model(torch.tensor(bte).to(dev), torch.tensor(rte).to(dev)).argmax(1).cpu().numpy()
    names = np.array(AAMI_CLASSES)
    row, cm = evaluate("CNN_1d", names[yte], names[pred])
    print(f"\nCNN_1d: acc={row['accuracy']:.4f} macro-F1={row['macro_F1']:.4f}\n{cm}")
    pd.DataFrame([row]).to_csv(RESULTS_DIR / "04_cnn_1d.csv", index=False)
    cm.to_csv(RESULTS_DIR / "04_confusion_CNN_1d.csv")
    torch.save({"model": model.state_dict(), "rr_mu": mu, "rr_sd": sd}, RESULTS_DIR / "cnn_1d.pt")


if __name__ == "__main__":
    main()
