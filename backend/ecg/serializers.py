from rest_framework import serializers

from .models import Annotation, Record


class RecordSerializer(serializers.ModelSerializer):
    duration_s = serializers.FloatField(read_only=True)
    annotation_count = serializers.IntegerField(source="annotations.count", read_only=True)

    class Meta:
        model = Record
        fields = ["id", "name", "dataset", "fs", "n_samples", "duration_s", "leads",
                  "annotation_count", "created_at"]


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ["id", "record", "start_sample", "end_sample", "lead", "label", "source",
                  "confidence", "verified", "annotator", "note", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        start = data.get("start_sample", getattr(self.instance, "start_sample", None))
        end = data.get("end_sample", getattr(self.instance, "end_sample", None))
        record = data.get("record", getattr(self.instance, "record", None))
        if start is not None and end is not None and end <= start:
            raise serializers.ValidationError("end_sample must be greater than start_sample.")
        if record is not None and end is not None and end > record.n_samples:
            raise serializers.ValidationError("Segment goes past the end of the record.")
        return data
