#!/usr/bin/env bash
set -euo pipefail
ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-health-source
VENV=/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin
SOCKET=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd
PORT=56422
DB_NAME="jobs_health_fixed_$(date -u +%Y%m%d%H%M%S)_$$"
CREATED=false
cleanup() {
  if [[ "$CREATED" == true ]]; then
    dropdb -h "$SOCKET" -p "$PORT" -U pchordia --if-exists "$DB_NAME" >/dev/null
  fi
}
trap cleanup EXIT
createdb -h "$SOCKET" -p "$PORT" -U pchordia "$DB_NAME"
CREATED=true
export JOBS_HEALTH_DIAGNOSTIC_DB="$DB_NAME"
export JOBS_HEALTH_SOURCE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
export PYTHONPATH="$ROOT/src:$ROOT"
"$VENV/python" /tmp/jobs-j20-health-begin-failure-fixed-20260922.py
# A separate process, with a new DB connection, verifies durable readback.
"$VENV/python" - <<'PY'
import os
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from jobs_automation.health import HealthCheckService
engine=create_engine(URL.create('postgresql+psycopg',username='pchordia',database=os.environ['JOBS_HEALTH_DIAGNOSTIC_DB'],query={'host':'/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd','port':'56422'}))
r=HealthCheckService(sessionmaker(bind=engine)).check_worker()
assert r.status=='DEGRADED' and r.details['last_attempt_status']=='FAILED'
assert r.details['last_error_category']=='BEGIN_RECORD_FAILED' and r.details['last_success_at']
print('SEPARATE_PROCESS_READBACK=DEGRADED/FAILED/BEGIN_RECORD_FAILED/PRIOR_SUCCESS_PRESERVED')
engine.dispose()
PY
dropdb -h "$SOCKET" -p "$PORT" -U pchordia "$DB_NAME"
CREATED=false
REMAINING=$(psql -h "$SOCKET" -p "$PORT" -U pchordia -d postgres -Atqc "SELECT count(*) FROM pg_database WHERE datname='$DB_NAME'")
echo "CLEANUP_DATABASE_COUNT=$REMAINING"
[[ "$REMAINING" == 0 ]]
