from django.db import models


class Record(models.Model):
    """One ECG recording (e.g. MIT-BIH record 100)."""

    name = models.CharField(max_length=100)
    dataset = models.CharField(max_length=50, default="MIT-BIH")
    file_path = models.CharField(max_length=255, help_text="WFDB path relative to ECG_DATA_DIR, no extension")
    fs = models.FloatField(help_text="Sampling rate (Hz)")
    n_samples = models.PositiveIntegerField()
    leads = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["dataset", "name"]
        unique_together = [("dataset", "name")]

    @property
    def duration_s(self):
        return self.n_samples / self.fs

    def __str__(self):
        return f"{self.dataset}/{self.name}"


class Label(models.TextChoices):
    NORMAL = "Normal", "Normal sinus rhythm"
    TACHY = "Tachycardia", "Tachycardia"
    BRADY = "Bradycardia", "Bradycardia"
    IRREGULAR = "Irregular", "Irregular rhythm"
    PAUSE = "Pause", "Pause"
    AF = "AF", "Atrial fibrillation"
    PVC = "PVC", "Premature ventricular contraction"
    APC = "APC", "Atrial premature contraction"
    NOISE = "Noise", "Noise / artefact"
    OTHER = "Other", "Other"


class Annotation(models.Model):
    """A labelled segment of a record — made by a person, the detector, or the dataset."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        AUTO = "auto", "Automatic (detector)"
        REFERENCE = "reference", "Dataset reference"

    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="annotations")
    start_sample = models.PositiveIntegerField()
    end_sample = models.PositiveIntegerField()
    lead = models.PositiveSmallIntegerField(default=0)
    label = models.CharField(max_length=20, choices=Label.choices)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    confidence = models.FloatField(null=True, blank=True)
    verified = models.BooleanField(default=False, help_text="Reviewed and accepted by a person")
    annotator = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["record", "start_sample"]
        indexes = [models.Index(fields=["record", "start_sample"], name="ecg_annotat_record__idx")]

    def __str__(self):
        return f"{self.record} {self.label} [{self.start_sample}-{self.end_sample}]"
