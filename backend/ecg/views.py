import csv

from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Annotation, Label, Record
from .serializers import AnnotationSerializer, RecordSerializer
from .services import get_window, run_detection


@api_view(["GET"])
def labels(request):
    return Response([{"value": v, "label": l} for v, l in Label.choices])


class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer

    @action(detail=True, methods=["get"])
    def signal(self, request, pk=None):
        """GET /api/records/{id}/signal/?start=0&end=3600&lead=0&filtered=1"""
        rec = self.get_object()
        start = int(request.query_params.get("start", 0))
        end = int(request.query_params.get("end", start + int(10 * rec.fs)))
        lead = int(request.query_params.get("lead", 0))
        filtered = request.query_params.get("filtered", "1") == "1"
        return Response(get_window(rec, start, end, lead, filtered))

    @action(detail=True, methods=["post"])
    def detect(self, request, pk=None):
        """POST /api/records/{id}/detect/  body: {"lead": 0, "rules": {...}}"""
        rec = self.get_object()
        created, summary = run_detection(rec, int(request.data.get("lead", 0)), request.data.get("rules"))
        return Response({"summary": summary,
                         "annotations": AnnotationSerializer(created, many=True).data},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """GET /api/records/{id}/export/?fmt=csv|json&verified_only=1"""
        rec = self.get_object()
        qs = rec.annotations.all()
        if request.query_params.get("verified_only") == "1":
            qs = qs.filter(verified=True) | qs.filter(source=Annotation.Source.MANUAL)
        rows = AnnotationSerializer(qs, many=True).data
        if request.query_params.get("fmt", "csv") == "json":
            return Response({"record": rec.name, "dataset": rec.dataset, "fs": rec.fs, "annotations": rows})
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{rec.dataset}_{rec.name}_annotations.csv"'
        fields = ["start_sample", "end_sample", "start_s", "end_s", "lead", "label",
                  "source", "confidence", "verified", "annotator", "note"]
        w = csv.DictWriter(resp, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r["start_s"] = round(r["start_sample"] / rec.fs, 3)
            r["end_s"] = round(r["end_sample"] / rec.fs, 3)
            w.writerow(r)
        return resp


class AnnotationViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        qs = Annotation.objects.all()
        p = self.request.query_params
        if p.get("record"):
            qs = qs.filter(record_id=p["record"])
        if p.get("start") and p.get("end"):   # annotations overlapping a window
            qs = qs.filter(end_sample__gt=int(p["start"]), start_sample__lt=int(p["end"]))
        if p.get("source"):
            qs = qs.filter(source=p["source"])
        return qs

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """Accept an automatic annotation (optionally with a corrected label)."""
        ann = self.get_object()
        if request.data.get("label"):
            ann.label = request.data["label"]
        ann.verified = True
        ann.annotator = request.data.get("annotator", ann.annotator)
        ann.save()
        return Response(AnnotationSerializer(ann).data)
