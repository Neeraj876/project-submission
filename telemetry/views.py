import hashlib
import hmac
import json

from django.db import IntegrityError
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import AppClient, HealthSample, default_health_rules

ALLOWED_CLOCK_SKEW_SECONDS = 300
MAX_LOOKBACK_MINUTES = 24 * 60


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _get_client(request):
    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key:
        return None
    try:
        return AppClient.objects.get(api_key=api_key, is_active=True)
    except AppClient.DoesNotExist:
        return None


def _parse_timestamp(header_value):
    try:
        ts = int(header_value)
    except (TypeError, ValueError):
        return None
    now_ts = int(timezone.now().timestamp())
    if abs(now_ts - ts) > ALLOWED_CLOCK_SKEW_SECONDS:
        return None
    return ts


def _valid_signature(client, timestamp, raw_body, signature):
    if not signature:
        return False
    message = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(client.secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _coerce_payload(payload):
    required = [
        "event_id",
        "request_count",
        "error_count",
        "avg_latency_ms",
        "p95_latency_ms",
        "cpu_percent",
        "memory_percent",
        "uptime_percent",
    ]
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    event_id = str(payload["event_id"]).strip()
    if not event_id:
        raise ValueError("event_id cannot be empty")

    request_count = int(payload["request_count"])
    error_count = int(payload["error_count"])
    avg_latency_ms = float(payload["avg_latency_ms"])
    p95_latency_ms = float(payload["p95_latency_ms"])
    cpu_percent = float(payload["cpu_percent"])
    memory_percent = float(payload["memory_percent"])
    uptime_percent = float(payload["uptime_percent"])
    if request_count < 0 or error_count < 0:
        raise ValueError("request_count and error_count must be >= 0")
    if error_count > request_count:
        raise ValueError("error_count cannot exceed request_count")
    for field_name, val in [
        ("cpu_percent", cpu_percent),
        ("memory_percent", memory_percent),
        ("uptime_percent", uptime_percent),
    ]:
        if val < 0 or val > 100:
            raise ValueError(f"{field_name} must be between 0 and 100")
    if avg_latency_ms < 0 or p95_latency_ms < 0:
        raise ValueError("latency values must be >= 0")

    captured_at_raw = payload.get("captured_at")
    if captured_at_raw:
        captured_at = parse_datetime(captured_at_raw)
        if captured_at is None:
            raise ValueError("captured_at must be ISO-8601 datetime")
    else:
        captured_at = timezone.now()

    if captured_at.tzinfo is None:
        captured_at = timezone.make_aware(captured_at)

    meta = payload.get("meta", {})
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ValueError("meta must be an object")

    return {
        "event_id": event_id,
        "request_count": request_count,
        "error_count": error_count,
        "avg_latency_ms": avg_latency_ms,
        "p95_latency_ms": p95_latency_ms,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "uptime_percent": uptime_percent,
        "captured_at": captured_at,
        "meta": meta,
    }


def _effective_rules(client):
    rules = default_health_rules()
    if isinstance(client.health_rules, dict):
        for key, value in client.health_rules.items():
            if key in rules:
                try:
                    rules[key] = float(value)
                except (TypeError, ValueError):
                    pass
    return rules


def _health_status(summary, rules):
    warning = []
    critical = []

    if summary["error_rate"] > rules["max_error_rate"]:
        critical.append("error_rate")
    if summary["avg_uptime_percent"] < rules["min_uptime_percent"]:
        critical.append("uptime")

    if summary["avg_p95_latency_ms"] > rules["max_p95_latency_ms"]:
        warning.append("latency")
    if summary["avg_cpu_percent"] > rules["max_cpu_percent"]:
        warning.append("cpu")
    if summary["avg_memory_percent"] > rules["max_memory_percent"]:
        warning.append("memory")

    if critical:
        return "critical", critical + warning
    if warning:
        return "warning", warning
    return "healthy", []


@csrf_exempt
def ingest(request):
    if request.method != "POST":
        return _error("POST only", status=405)

    client = _get_client(request)
    if client is None:
        return _error("Invalid API key", status=401)

    raw_body = request.body
    timestamp = _parse_timestamp(request.headers.get("X-Timestamp"))
    if timestamp is None:
        return _error("Invalid or stale X-Timestamp", status=401)

    signature = request.headers.get("X-Signature", "").strip()
    if not _valid_signature(client, timestamp, raw_body, signature):
        return _error("Bad signature", status=401)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
        metric = _coerce_payload(payload)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Body must be valid JSON")
    except ValueError as exc:
        return _error(str(exc))

    try:
        HealthSample.objects.create(app=client, **metric)
    except IntegrityError:
        return _error("Duplicate event_id for this app", status=409)

    return JsonResponse({"status": "accepted"}, status=202)


def health(request):
    client = _get_client(request)
    if client is None:
        return _error("Invalid API key", status=401)

    lookback_raw = request.GET.get("minutes", "15")
    try:
        lookback_minutes = int(lookback_raw)
    except ValueError:
        return _error("minutes must be an integer")
    if lookback_minutes < 1 or lookback_minutes > MAX_LOOKBACK_MINUTES:
        return _error(f"minutes must be between 1 and {MAX_LOOKBACK_MINUTES}")

    window_start = timezone.now() - timezone.timedelta(minutes=lookback_minutes)
    qs = HealthSample.objects.filter(app=client, captured_at__gte=window_start)
    latest = qs.order_by("-captured_at").first()

    if latest is None:
        return JsonResponse(
            {
                "app": client.name,
                "window_minutes": lookback_minutes,
                "status": "unknown",
                "message": "No telemetry in selected window",
            }
        )

    agg = qs.aggregate(
        total_requests=Sum("request_count"),
        total_errors=Sum("error_count"),
        avg_latency_ms=Avg("avg_latency_ms"),
        avg_p95_latency_ms=Avg("p95_latency_ms"),
        avg_cpu_percent=Avg("cpu_percent"),
        avg_memory_percent=Avg("memory_percent"),
        avg_uptime_percent=Avg("uptime_percent"),
    )
    total_requests = agg["total_requests"] or 0
    total_errors = agg["total_errors"] or 0
    error_rate = (total_errors / total_requests * 100.0) if total_requests else 0.0

    summary = {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate": round(error_rate, 2),
        "avg_latency_ms": round(agg["avg_latency_ms"] or 0.0, 2),
        "avg_p95_latency_ms": round(agg["avg_p95_latency_ms"] or 0.0, 2),
        "avg_cpu_percent": round(agg["avg_cpu_percent"] or 0.0, 2),
        "avg_memory_percent": round(agg["avg_memory_percent"] or 0.0, 2),
        "avg_uptime_percent": round(agg["avg_uptime_percent"] or 0.0, 2),
    }

    rules = _effective_rules(client)
    status, breached = _health_status(summary, rules)

    return JsonResponse(
        {
            "app": client.name,
            "window_minutes": lookback_minutes,
            "status": status,
            "breached_rules": breached,
            "rules": rules,
            "summary": summary,
            "latest": {
                "event_id": latest.event_id,
                "captured_at": latest.captured_at.isoformat(),
                "request_count": latest.request_count,
                "error_count": latest.error_count,
                "avg_latency_ms": latest.avg_latency_ms,
                "p95_latency_ms": latest.p95_latency_ms,
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "uptime_percent": latest.uptime_percent,
            },
        }
    )
