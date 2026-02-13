from django.urls import path
from . import views

urlpatterns = [
    path("ingest/", views.ingest, name="telemetry_ingest"),
    path("health/", views.health, name="telemetry_health"),
]
