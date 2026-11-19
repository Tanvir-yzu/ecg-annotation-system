from django.contrib import admin

from .models import Annotation, Record


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("name", "dataset", "fs", "n_samples", "created_at")
    list_filter = ("dataset",)
    search_fields = ("name",)


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ("record", "label", "source", "verified", "start_sample", "end_sample", "annotator")
    list_filter = ("label", "source", "verified", "record__dataset")
