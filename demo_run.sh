#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PY=".venv/Scripts/python.exe"

WIN_USER="${USERNAME:-${USER:-${LOGNAME:-user}}}"
DEFAULT_DB_PATH="/c/Users/${WIN_USER}/AppData/Local/Temp/knowella_demo.sqlite3"
export KNOWELLA_DB_PATH="${KNOWELLA_DB_PATH:-$DEFAULT_DB_PATH}"

"$PY" manage.py makemigrations
"$PY" manage.py migrate
"$PY" manage.py check

"$PY" manage.py run_datajob --config dataops/job_csv_to_csv.yaml
"$PY" manage.py run_datajob --config dataops/job_csv_to_db.yaml
"$PY" manage.py run_datajob --config dataops/job_excel_to_csv.yaml
"$PY" manage.py run_datajob --config dataops/job_excel_to_db.yaml
cat output/paid_orders.csv
cat output/paid_orders_from_excel.csv
"$PY" manage.py shell -c "from dataops.models import DataRun,DataRecord; print('Q5 DataRuns=',DataRun.objects.count()); print('Q5 DataRecords=',DataRecord.objects.count())"

"$PY" manage.py shell -c "import json,hmac,hashlib,time; from django.test import Client; from telemetry.models import AppClient; AppClient.objects.update_or_create(name='demo-web', defaults={'api_key':'demo-key','secret':'demo-secret','is_active':True}); c=Client(HTTP_HOST='localhost'); payload={'event_id':'evt-demo-001','request_count':1200,'error_count':12,'avg_latency_ms':145.5,'p95_latency_ms':420.3,'cpu_percent':63.5,'memory_percent':71.2,'uptime_percent':99.94,'meta':{'env':'demo'}}; raw=json.dumps(payload,separators=(',',':')); ts=str(int(time.time())); sig=hmac.new(b'demo-secret', f'{ts}.{raw}'.encode('utf-8'), hashlib.sha256).hexdigest(); r1=c.post('/telemetry/ingest/', data=raw, content_type='application/json', HTTP_X_API_KEY='demo-key', HTTP_X_TIMESTAMP=ts, HTTP_X_SIGNATURE=sig); r2=c.get('/telemetry/health/?minutes=15', HTTP_X_API_KEY='demo-key'); print('Q6 ingest=', r1.status_code, r1.json()); print('Q6 health=', r2.status_code, r2.json().get('status'))"

"$PY" manage.py seed_hot_topics --reset
"$PY" manage.py rebuild_hot_topics
"$PY" manage.py shell -c "from django.test import Client; c=Client(HTTP_HOST='localhost'); r1=c.get('/'); r2=c.get('/category/technology/'); r3=c.get('/api/hot-topics/'); r4=c.get('/api/category/technology/search/?q=ai'); r5=c.get('/category/technology/search/?q=ai', HTTP_HX_REQUEST='true'); print('Q10 home=', r1.status_code); print('Q10 category=', r2.status_code); print('Q10 api_hot=', r3.status_code, r3.json().get('count')); print('Q10 api_search=', r4.status_code, r4.json().get('count')); print('Q10 htmx_partial=', r5.status_code)"

echo "All checks completed."
echo "Run server: python manage.py runserver"
