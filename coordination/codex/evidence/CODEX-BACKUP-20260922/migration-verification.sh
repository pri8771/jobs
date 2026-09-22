#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-backup-source
VENV=/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin
SOCKET=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd
PORT=56422
USER_NAME=pchordia
DB_NAME="jobs_migration_probe_$(date -u +%Y%m%d%H%M%S)_$$"
CREATED=false

cleanup() {
  if [[ "$CREATED" == true ]]; then
    dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" --if-exists "$DB_NAME" >/dev/null
  fi
}
trap cleanup EXIT

createdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$DB_NAME"
CREATED=true
ENCODED_SOCKET=$($VENV/python -c 'import urllib.parse; print(urllib.parse.quote("/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd", safe=""))')
export DATABASE_URL="postgresql+psycopg://${USER_NAME}@/${DB_NAME}?host=${ENCODED_SOCKET}&port=${PORT}"
export PATH="$VENV:$PATH"

echo "SOURCE_SHA=$(git -C "$ROOT" rev-parse HEAD)"
echo "SCRIPT_SHA256=$(shasum -a 256 "$ROOT/scripts/verify_migrations.sh" | awk '{print $1}')"
echo "DATABASE=$DB_NAME"

(
  cd "$ROOT"
  bash scripts/verify_migrations.sh
)

REVISION=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$DB_NAME" -Atqc \
  'SELECT version_num FROM alembic_version')
HEAD=$(
  cd "$ROOT"
  alembic heads | awk '{print $1}' | head -n 1
)
TABLE_COUNT=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$DB_NAME" -Atqc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
echo "OBSERVED_REVISION=$REVISION"
echo "ALEMBIC_HEAD=$HEAD"
echo "PUBLIC_TABLE_COUNT=$TABLE_COUNT"
[[ "$REVISION" == "$HEAD" ]]

dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$DB_NAME"
CREATED=false
REMAINING=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d postgres -Atqc \
  "SELECT count(*) FROM pg_database WHERE datname='$DB_NAME'")
echo "CLEANUP_DATABASE_COUNT=$REMAINING"
[[ "$REMAINING" == 0 ]]
