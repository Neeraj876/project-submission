from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def default_health_rules():
    return {
        "max_error_rate": 2.0,
        "max_p95_latency_ms": 800.0,
        "min_uptime_percent": 99.0,
        "max_cpu_percent": 90.0,
        "max_memory_percent": 90.0,
    }


class AppClient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    api_key = models.CharField(max_length=64, unique=True)
    secret = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    health_rules = models.JSONField(default=default_health_rules)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class HealthSample(models.Model):
    app = models.ForeignKey(AppClient, on_delete=models.CASCADE, related_name="samples")
    event_id = models.CharField(max_length=64)
    captured_at = models.DateTimeField()
    request_count = models.PositiveIntegerField()
    error_count = models.PositiveIntegerField()
    avg_latency_ms = models.FloatField(validators=[MinValueValidator(0.0)])
    p95_latency_ms = models.FloatField(validators=[MinValueValidator(0.0)])
    cpu_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    memory_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    uptime_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    meta = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["app", "event_id"], name="unique_event_per_app"
            )
        ]
        indexes = [
            models.Index(fields=["app", "captured_at"]),
            models.Index(fields=["captured_at"]),
        ]

    def __str__(self):
        return f"{self.app.name} @ {self.captured_at.isoformat()}"
