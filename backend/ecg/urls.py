from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnnotationViewSet, RecordViewSet, labels

router = DefaultRouter()
router.register("records", RecordViewSet)
router.register("annotations", AnnotationViewSet, basename="annotation")

urlpatterns = [
    path("labels/", labels),
    path("", include(router.urls)),
]
