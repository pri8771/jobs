#!/usr/bin/env bash
set -euo pipefail
ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-integration-source
VENV=/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin
SOCKET=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd
PORT=56422
DB_NAME="jobs_integration_remaining_$(date -u +%Y%m%d%H%M%S)_$$"
CREATED=false
cleanup() {
  if [[ "$CREATED" == true ]]; then
    dropdb -h "$SOCKET" -p "$PORT" -U pchordia --if-exists "$DB_NAME" >/dev/null
  fi
}
trap cleanup EXIT
createdb -h "$SOCKET" -p "$PORT" -U pchordia "$DB_NAME"
CREATED=true
export JOBS_HEALTH_DB="$DB_NAME"
export JOBS_SOURCE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
export PYTHONPATH="$ROOT/src:$ROOT"
"$VENV/python" /tmp/jobs-integration-health-remaining-pg.py
dropdb -h "$SOCKET" -p "$PORT" -U pchordia "$DB_NAME"
CREATED=false
REMAINING=$(psql -h "$SOCKET" -p "$PORT" -U pchordia -d postgres -Atqc "SELECT count(*) FROM pg_database WHERE datname='$DB_NAME'")
echo "CLEANUP_DATABASE_COUNT=$REMAINING"
[[ "$REMAINING" == 0 ]]
