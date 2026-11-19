"""Shared helpers for experiments. Run every script from backend/:  python experiments/01_rpeak_eval.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data" / "mitdb"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def ensure_mitbih():
    """Download MIT-BIH if it is not in data/mitdb yet."""
    if not any(DATA_DIR.glob("*.hea")):
        from ecg_core.io import download_mitbih
        print("MIT-BIH not found — downloading to", DATA_DIR)
        download_mitbih(DATA_DIR)


def record_ids():
    return sorted(int(p.stem) for p in DATA_DIR.glob("*.hea"))
