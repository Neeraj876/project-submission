# Knowella Django Assignment Submission

This repository implements the following questions from the assignment:

1. Q5: Config-driven CSV/Excel processing and output to CSV/DB (`dataops`)
2. Q6: Lightweight secure telemetry system for web app health metrics (`telemetry`)
3. Q10: Hot topics feature with top 20 trending posts + category search (`hot_topics`)

## Tech Stack

1. Python 3.12+
2. Django 6
3. SQLite
4. Pandas, OpenPyXL, PyYAML
5. HTMX (for live search in Q10)

## Run the Project

Clone and enter repository:

```bash
git clone https://github.com/Neeraj876/project-submission.git
cd project-submission
python -m venv .venv
```

Git Bash:

```bash
source .venv/Scripts/activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install django djangorestframework pandas openpyxl pyyaml
```

If SQLite gives `disk I/O error`, set temp DB path:

Git Bash:

```bash
export KNOWELLA_DB_PATH="/c/Users/$USERNAME/AppData/Local/Temp/knowella_submission.sqlite3"
```

PowerShell:

```powershell
$env:KNOWELLA_DB_PATH="$env:TEMP\knowella_submission.sqlite3"
```

Migrate and start server:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## One-Command Demo

Run from repository root:

```bash
bash demo_run.sh
```

What this script runs:

1. migrations + Django system check
2. Q5 all config variants (CSV/Excel to CSV/DB)
3. Q6 secure ingest + health response
4. Q10 seed, ranking rebuild, page/API/HTMX route checks

## Main Routes

1. Q10 landing page: `http://127.0.0.1:8000/`
2. Q5 app page: `http://127.0.0.1:8000/dataops/`
3. Q6 health endpoint: `http://127.0.0.1:8000/telemetry/health/?minutes=15`

## Q5 Run and Check (DataOps)

Run config-based jobs:

```bash
python manage.py run_datajob --config dataops/job.yaml
python manage.py run_datajob --config dataops/job_excel_to_csv.yaml
python manage.py run_datajob --config dataops/job_excel_to_db.yaml
python manage.py run_datajob --config dataops/job_csv_to_csv.yaml
python manage.py run_datajob --config dataops/job_csv_to_db.yaml
```

Check outputs:

```bash
cat output/paid_orders.csv
cat output/paid_orders_from_excel.csv
python manage.py shell -c "from dataops.models import DataRecord; print(DataRecord.objects.count())"
```

Supported actions in config:

1. `select`
2. `filter`
3. `rename`
4. `cast`
5. `compute`
6. `dedupe`
7. `sort`

## Q6 Run and Check (Telemetry)

Create API credentials:

```bash
python manage.py create_app_client --name demo-web
```

Send one signed telemetry event (replace placeholders):

```bash
python - <<'PY'
import json, time, hmac, hashlib, urllib.request

api_key = "REPLACE_WITH_API_KEY"
secret = "REPLACE_WITH_SECRET"

payload = {
    "event_id": "evt-001",
    "request_count": 1200,
    "error_count": 12,
    "avg_latency_ms": 145.5,
    "p95_latency_ms": 420.3,
    "cpu_percent": 63.5,
    "memory_percent": 71.2,
    "uptime_percent": 99.94,
    "meta": {"env": "dev"}
}

raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
ts = str(int(time.time()))
sig = hmac.new(secret.encode("utf-8"), f"{ts}.{raw.decode('utf-8')}".encode("utf-8"), hashlib.sha256).hexdigest()

req = urllib.request.Request(
    "http://127.0.0.1:8000/telemetry/ingest/",
    data=raw,
    method="POST",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "X-Timestamp": ts,
        "X-Signature": sig,
    },
)
print("INGEST:", urllib.request.urlopen(req).read().decode())

health_req = urllib.request.Request(
    "http://127.0.0.1:8000/telemetry/health/?minutes=15",
    headers={"X-API-Key": api_key},
)
print("HEALTH:", urllib.request.urlopen(health_req).read().decode())
PY
```

Expected behavior:

1. Ingest returns `{"status": "accepted"}`
2. Health returns JSON with summary and status
3. Duplicate `event_id` for same app returns `409`

## Q10 Run and Check (Hot Topics)

Seed and compute rankings:

```bash
python manage.py seed_hot_topics --reset
python manage.py rebuild_hot_topics
```

Open and check:

1. `http://127.0.0.1:8000/` (global top 20)
2. `http://127.0.0.1:8000/category/technology/` (category page)
3. Category search updates live using HTMX
4. `http://127.0.0.1:8000/api/hot-topics/` (JSON top 20)
5. `http://127.0.0.1:8000/api/category/technology/search/?q=ai` (category search API)

## Notes

1. Keep API keys/secrets out of committed files.
2. This submission is built for assignment demo scope (SQLite + management commands + APIs).
