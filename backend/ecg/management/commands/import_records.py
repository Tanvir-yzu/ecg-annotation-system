"""Import WFDB records into the database.

Examples (run from backend/):
  python manage.py import_records --download              # download MIT-BIH, then import
  python manage.py import_records --dir data/mitdb --dataset MIT-BIH --reference
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ecg.models import Annotation, Record

# MIT-BIH rhythm codes (aux_note) -> system labels
RHYTHM_MAP = {"(N": "Normal", "(SBR": "Bradycardia", "(SVTA": "Tachycardia", "(VT": "Tachycardia",
              "(AFIB": "AF", "(AFL": "Other", "(B": "Other", "(T": "Other", "(IVR": "Other",
              "(NOD": "Other", "(P": "Other", "(PREX": "Other", "(BII": "Other", "(VFL": "Other"}


class Command(BaseCommand):
    help = "Import WFDB records (and optionally their reference rhythm annotations)."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="data/mitdb", help="Folder with .hea/.dat files (relative to backend/)")
        parser.add_argument("--dataset", default="MIT-BIH")
        parser.add_argument("--download", action="store_true", help="Download MIT-BIH from PhysioNet first")
        parser.add_argument("--reference", action="store_true", help="Import dataset rhythm labels as reference annotations")

    def handle(self, *args, **opts):
        import wfdb
        from ecg_core.io import download_mitbih

        folder = Path(opts["dir"])
        if not folder.is_absolute():
            folder = settings.BASE_DIR / folder
        if opts["download"]:
            self.stdout.write("Downloading MIT-BIH (~100 MB)...")
            download_mitbih(folder)

        heads = sorted(folder.glob("*.hea"))
        if not heads:
            self.stderr.write(f"No .hea files in {folder}")
            return

        for hea in heads:
            path = hea.with_suffix("")
            h = wfdb.rdheader(str(path))
            try:
                rel = path.relative_to(settings.ECG_DATA_DIR).as_posix()
            except ValueError:  # folder outside data/ -> store absolute path
                rel = path.resolve().as_posix()
            rec, created = Record.objects.update_or_create(
                dataset=opts["dataset"], name=hea.stem,
                defaults={"file_path": rel, "fs": float(h.fs), "n_samples": int(h.sig_len),
                          "leads": list(h.sig_name)})
            n_ref = self._import_reference(rec, path) if opts["reference"] else 0
            self.stdout.write(f"{'+' if created else '~'} {rec}  ({rec.duration_s / 60:.1f} min, {n_ref} reference segments)")

    def _import_reference(self, rec, path):
        """Turn MIT-BIH rhythm-change markers into reference segments."""
        import wfdb

        if not Path(str(path) + ".atr").exists():
            return 0
        ann = wfdb.rdann(str(path), "atr")
        rec.annotations.filter(source=Annotation.Source.REFERENCE).delete()
        marks = [(int(s), a.strip("\x00")) for s, a in zip(ann.sample, ann.aux_note) if a.strip("\x00").startswith("(")]
        objs = []
        for i, (start, code) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else rec.n_samples
            if end > start:
                objs.append(Annotation(record=rec, start_sample=start, end_sample=end,
                                       label=RHYTHM_MAP.get(code, "Other"),
                                       source=Annotation.Source.REFERENCE, verified=True,
                                       annotator="dataset", note=code))
        Annotation.objects.bulk_create(objs)
        return len(objs)
