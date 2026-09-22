#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-backup-source
PG_SOCKET=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd
PG_PORT=56422
PG_USER=pchordia
DB_NAME="jobs_restore_probe_$(date -u +%Y%m%d%H%M%S)_$$"
CASE_ROOT=$(mktemp -d /tmp/jobs-v20-restore-on-error.XXXXXX)
CREATED=false

cleanup() {
  if [[ "$CREATED" == true ]]; then
    dropdb -h "$PG_SOCKET" -p "$PG_PORT" -U "$PG_USER" --if-exists "$DB_NAME" >/dev/null
  fi
  rm -rf "$CASE_ROOT"
}
trap cleanup EXIT

createdb -h "$PG_SOCKET" -p "$PG_PORT" -U "$PG_USER" "$DB_NAME"
CREATED=true

cat > "$CASE_ROOT/malformed.sql" <<'SQL'
CREATE TABLE restore_probe(id integer PRIMARY KEY);
INSERT INTO restore_probe VALUES (1);
THIS IS DELIBERATELY INVALID SQL;
INSERT INTO restore_probe VALUES (2);
SQL
gzip -9 -c "$CASE_ROOT/malformed.sql" > "$CASE_ROOT/malformed.sql.gz"
shasum -a 256 "$CASE_ROOT/malformed.sql.gz" > "$CASE_ROOT/malformed.sql.gz.sha256"

echo "SOURCE_SHA=$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
echo "SCRIPT_SHA256=$(shasum -a 256 "$SOURCE_ROOT/scripts/restore_db.sh" | awk '{print $1}')"
echo "DATABASE=$DB_NAME"
echo "ARCHIVE_HASH=$(shasum -a 256 "$CASE_ROOT/malformed.sql.gz" | awk '{print $1}')"

set +e
DB_HOST="$PG_SOCKET" DB_PORT="$PG_PORT" DB_USER="$PG_USER" DB_NAME="$DB_NAME" \
  DB_PASSWORD=synthetic-local-placeholder \
  "$SOURCE_ROOT/scripts/restore_db.sh" "$CASE_ROOT/malformed.sql.gz" --force
RESTORE_STATUS=$?
set -e

TABLE_NAME=$(psql -h "$PG_SOCKET" -p "$PG_PORT" -U "$PG_USER" -d "$DB_NAME" \
  -Atqc "SELECT COALESCE(to_regclass('public.restore_probe')::text, 'ABSENT')")
echo "RESTORE_EXIT=$RESTORE_STATUS"
echo "RESTORE_PROBE_TABLE=$TABLE_NAME"

dropdb -h "$PG_SOCKET" -p "$PG_PORT" -U "$PG_USER" "$DB_NAME"
CREATED=false
REMAINING=$(psql -h "$PG_SOCKET" -p "$PG_PORT" -U "$PG_USER" -d postgres -Atqc \
  "SELECT count(*) FROM pg_database WHERE datname = '$DB_NAME'")
echo "CLEANUP_DATABASE_COUNT=$REMAINING"

if [[ "$RESTORE_STATUS" -eq 0 && "$TABLE_NAME" == "ABSENT" && "$REMAINING" == "0" ]]; then
  echo "OBSERVED=restore reported success although malformed SQL aborted and rolled back the transaction"
  exit 0
fi
echo "OBSERVED=behavior differed from suspected silent-success failure"
exit 91
