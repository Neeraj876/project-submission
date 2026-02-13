# Knowella Assignment Submission

Django project implementing three assignment questions:

- Q5: Config-driven CSV/Excel data processing (`dataops`)
- Q6: Lightweight secure telemetry system (`telemetry`)
- Q10: Hot topics/trending feed with category search (`hot_topics`)

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Run the Project](#run-the-project)
- [Q5: DataOps](#q5-dataops)
- [Q6: Telemetry](#q6-telemetry)
- [Q10: Hot Topics](#q10-hot-topics)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

## Overview

This is a single Django codebase with modular apps for each problem statement.

Design goals:

- Keep each domain isolated by app
- Make behavior configurable (Q5)
- Keep telemetry secure but lightweight (Q6)
- Optimize hot-topic reads using precomputed rankings (Q10)

## Tech Stack

- Python 3.12+
- Django 6
- SQLite (default)
- Pandas, OpenPyXL, PyYAML
- HTMX (Q10 live search)

## Project Structure

```text
knowella/                     # project settings and root URLs
  settings.py
  urls.py

dataops/                      # Q5
  models.py
  services.py
  management/commands/run_datajob.py
  job.yaml
  job_excel_to_csv.yaml
  job_excel_to_db.yaml

telemetry/                    # Q6
  models.py
  views.py
  urls.py
  management/commands/create_app_client.py

hot_topics/                   # Q10
  models.py
  services.py
  views.py
  urls.py
  management/commands/seed_hot_topics.py
  management/commands/rebuild_hot_topics.py

templates/hot_topics/
  home.html
  category.html
  _search_results.html
```

## Getting Started

### 1) Create and activate virtual environment

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
python -m pip install django djangorestframework pandas openpyxl pyyaml
```

### 3) Optional SQLite workaround

If you see `sqlite3.OperationalError: disk I/O error`, use temp DB path:

Git Bash:

```bash
export KNOWELLA_DB_PATH="/c/Users/$USERNAME/AppData/Local/Temp/knowella_submission.sqlite3"
```

PowerShell:

```powershell
$env:KNOWELLA_DB_PATH="$env:TEMP\knowella_submission.sqlite3"
```

## Run the Project

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Main routes:

- `http://127.0.0.1:8000/` (Q10 landing)
- `http://127.0.0.1:8000/dataops/` (Q5 app)
- `http://127.0.0.1:8000/telemetry/health/?minutes=15` (Q6 health endpoint)

---

## Q5: DataOps

### What it does

Reads CSV/Excel, applies configurable transformations, writes to CSV or DB.

### Supported actions

- `select`
- `filter`
- `rename`
- `cast`
- `compute`
- `dedupe`
- `sort`

### Run examples

CSV -> CSV:

```bash
python manage.py run_datajob --config dataops/job.yaml
```

Excel -> CSV:

```bash
python manage.py run_datajob --config dataops/job_excel_to_csv.yaml
```

Excel -> DB:

```bash
python manage.py run_datajob --config dataops/job_excel_to_db.yaml
```

### Verify

```bash
cat output/paid_orders.csv
cat output/paid_orders_from_excel.csv
python manage.py shell -c "from dataops.models import DataRecord; print(DataRecord.objects.count())"
```

---

## Q6: Telemetry

### What it does

- Accepts telemetry samples via `POST /telemetry/ingest/`
- Validates API key + HMAC signature + timestamp freshness
- Computes app health summary via `GET /telemetry/health/?minutes=...`

### Security model

- `X-API-Key`: client identity
- `X-Timestamp`: anti-replay freshness check
- `X-Signature`: `HMAC_SHA256(secret, "{timestamp}.{raw_json}")`
- duplicate `event_id` (per app) blocked by DB uniqueness

### Metrics captured

- `request_count`
- `error_count`
- `avg_latency_ms`
- `p95_latency_ms`
- `cpu_percent`
- `memory_percent`
- `uptime_percent`

### Create client credentials

```bash
python manage.py create_app_client --name demo-web
```

### Send sample telemetry

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

---

## Q10: Hot Topics

### What it does

- Computes trending score using engagement + time decay
- Stores top rankings in `HotPost` for fast reads
- Serves top 20 on landing page (`/`)
- Supports category search
- Uses HTMX for live search updates without full page reload

### Ranking formula

```text
engagement = likes + 2*comments + 3*shares + 0.05*log1p(views)
score = (engagement + 1) / (1 + age_hours/6)
```

### Seed and build rankings

```bash
python manage.py seed_hot_topics --reset
python manage.py rebuild_hot_topics
```

### Verify endpoints

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/category/technology/`
- `http://127.0.0.1:8000/api/hot-topics/`
- `http://127.0.0.1:8000/api/category/technology/search/?q=ai`

---

## Troubleshooting

- `sqlite3.OperationalError: disk I/O error`
  - set `KNOWELLA_DB_PATH` to temp path and rerun migrations
- `Invalid API key` in telemetry
  - create a client again with `create_app_client`
- `Bad signature` in telemetry
  - ensure exact signature message format `"{timestamp}.{raw_json}"`
- Hot topics page empty
  - run `seed_hot_topics --reset` and `rebuild_hot_topics`

## Security Notes

- Do not commit real API keys/secrets
- Rotate credentials if exposed
- Use `DEBUG=False` and a stronger DB setup in production
