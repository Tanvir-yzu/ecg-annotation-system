# ECG Data Annotation and Abnormal Identification System for Cardiac Rhythm Analysis

Bachelor's thesis project: a web system to **view, annotate and automatically screen ECG recordings**, plus the offline experiments that measure how well the detection works.

```
ECG dataset (MIT-BIH / PTB-XL)
      │
      ▼
ecg_core: filter → R-peak detection → heart rate → rule-based rhythm events / ML beat classes
      │
      ▼
Django REST API ──► React + ECharts annotation tool
      │                 • ECG-paper waveform, zoom, scroll
      │                 • drag to select a segment → label → save
      │                 • "Run detection" → auto labels → accept / correct / delete
      ▼
Annotations DB (manual | auto | reference)  ──►  CSV / JSON export
```

## Project layout

```
backend/
  ecg_core/            framework-free signal processing (used by the web app AND experiments)
    preprocess.py      band-pass filter, baseline removal
    rpeaks.py          Pan-Tompkins-style R-peak detector + Se/PPV evaluation
    rhythm.py          rule-based tachycardia / bradycardia / irregular / pause detection
    beats.py           AAMI classes, beat segmentation, RR + morphology features
    splits.py          inter-patient DS1/DS2 split of MIT-BIH
    io.py              WFDB loading, MIT-BIH download
  ecg/                 Django app: models, REST API, import command
  config/              Django settings
  experiments/         thesis experiments → results/
  tests/               unit tests on synthetic ECG
  data/                datasets go here (git-ignored)
frontend/              React + Vite + ECharts annotation UI
```

## 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m pytest tests -q             # 6 tests, synthetic ECG, no download needed
python manage.py migrate
python manage.py import_records --download --reference   # downloads MIT-BIH (~100 MB) into data/mitdb
python manage.py createsuperuser      # optional, for /admin
python manage.py runserver            # API at http://localhost:8000/api/
```

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev                           # open http://localhost:5173
```

Set `VITE_API_URL` if the API is not at `http://localhost:8000/api`.

## 3. Using the annotation tool

1. Pick a record on the left.
2. Move through the recording with ◀ ▶, change lead / window length / filtering.
3. **Drag across the ECG** to select a segment, choose a label, press *Save annotation*.
4. **Run detection** creates automatic annotations (dashed). Review each: *Accept*, change its label (counts as a correction), or *Delete*.
5. **Export CSV** downloads all annotations for the record.

## 4. Experiments (thesis results)

Run from `backend/`. Each script downloads MIT-BIH if it is missing and writes to `backend/results/`.

| Script | What it measures | Thesis use |
|---|---|---|
| `python experiments/01_rpeak_eval.py` | R-peak Se / PPV / F1 on all 48 records | signal-processing chapter, CV number |
| `python experiments/02_rhythm_rules.py 203` | rule-based events + heart-rate figure | detection chapter figure |
| `python experiments/03_beat_classifier.py` | RF vs LogReg, AAMI N/S/V/F/Q, inter-patient | baseline comparison table |
| `python experiments/04_cnn_1d.py` | 1D-CNN (needs `pip install torch`) | main model vs baselines |

**Important:** experiments 3–4 use the **inter-patient** split (train DS1, test DS2, different patients). Never report intra-patient accuracy as the main result — it is inflated and reviewers know it.

## 5. REST API

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/labels/` | label list |
| GET | `/api/records/` | records |
| GET | `/api/records/{id}/signal/?start=&end=&lead=&filtered=1` | down-sampled window + R peaks |
| POST | `/api/records/{id}/detect/` | run rule-based detection → auto annotations |
| GET | `/api/records/{id}/export/?fmt=csv\|json` | export annotations |
| GET/POST | `/api/annotations/?record={id}` | list / create |
| PATCH/DELETE | `/api/annotations/{id}/` | edit / delete |
| POST | `/api/annotations/{id}/verify/` | accept an auto annotation (optionally relabel) |

## 6. Thesis roadmap

- [x] Project setup, ecg_core, API, annotation UI
- [ ] Run experiment 1, record R-peak Se/PPV
- [ ] Tune rhythm rules; compare against MIT-BIH reference rhythm labels
- [ ] Experiments 3–4: baseline vs 1D-CNN table + confusion matrices
- [ ] Add PTB-XL import + rhythm evaluation (generalisation)
- [ ] Annotation-time study: manual vs AI pre-labelled (2–3 annotators)
- [ ] Screenshots, demo video, thesis chapters, arXiv preprint

## Datasets

- MIT-BIH Arrhythmia Database — PhysioNet (`mitdb`), 48 two-lead records, 360 Hz, ~30 min each.
- PTB-XL — PhysioNet (`ptb-xl`), 12-lead, 10 s records with diagnostic and rhythm statements.

Cite both datasets and PhysioNet in the thesis.
