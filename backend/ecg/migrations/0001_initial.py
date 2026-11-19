import django.db.models.deletion
from django.db import migrations, models

LABELS = [
    ("Normal", "Normal sinus rhythm"), ("Tachycardia", "Tachycardia"), ("Bradycardia", "Bradycardia"),
    ("Irregular", "Irregular rhythm"), ("Pause", "Pause"), ("AF", "Atrial fibrillation"),
    ("PVC", "Premature ventricular contraction"), ("APC", "Atrial premature contraction"),
    ("Noise", "Noise / artefact"), ("Other", "Other"),
]


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Record",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("dataset", models.CharField(default="MIT-BIH", max_length=50)),
                ("file_path", models.CharField(help_text="WFDB path relative to ECG_DATA_DIR, no extension", max_length=255)),
                ("fs", models.FloatField(help_text="Sampling rate (Hz)")),
                ("n_samples", models.PositiveIntegerField()),
                ("leads", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["dataset", "name"], "unique_together": {("dataset", "name")}},
        ),
        migrations.CreateModel(
            name="Annotation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_sample", models.PositiveIntegerField()),
                ("end_sample", models.PositiveIntegerField()),
                ("lead", models.PositiveSmallIntegerField(default=0)),
                ("label", models.CharField(choices=LABELS, max_length=20)),
                ("source", models.CharField(choices=[("manual", "Manual"), ("auto", "Automatic (detector)"),
                                                     ("reference", "Dataset reference")],
                                            default="manual", max_length=10)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("verified", models.BooleanField(default=False, help_text="Reviewed and accepted by a person")),
                ("annotator", models.CharField(blank=True, max_length=100)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="annotations", to="ecg.record")),
            ],
            options={
                "ordering": ["record", "start_sample"],
                "indexes": [models.Index(fields=["record", "start_sample"], name="ecg_annotat_record__idx")],
            },
        ),
    ]
