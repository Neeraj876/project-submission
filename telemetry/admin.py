from django.contrib import admin

from .models import AppClient, HealthSample


@admin.register(AppClient)
class AppClientAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key", "is_active", "created_at")
    search_fields = ("name", "api_key")


@admin.register(HealthSample)
class HealthSampleAdmin(admin.ModelAdmin):
    list_display = (
        "app",
        "event_id",
        "captured_at",
        "request_count",
        "error_count",
        "p95_latency_ms",
        "uptime_percent",
    )
    list_filter = ("app", "captured_at")
    search_fields = ("event_id",)

# Register your models here.
