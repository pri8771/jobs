#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-integration-source
SOCKET=/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd
PORT=56422
USER_NAME=pchordia
STAMP="$(date -u +%Y%m%d%H%M%S)_$$"
SOURCE_DB="jobs_int_bak_src_${STAMP}"
TARGET_DB="jobs_int_bak_dst_${STAMP}"
CASE_ROOT=$(mktemp -d /tmp/jobs-v20-bak-repaired.XXXXXX)
SOURCE_CREATED=false
TARGET_CREATED=false

cleanup() {
  if [[ "$SOURCE_CREATED" == true ]]; then dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" --if-exists "$SOURCE_DB" >/dev/null; fi
  if [[ "$TARGET_CREATED" == true ]]; then dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" --if-exists "$TARGET_DB" >/dev/null; fi
  rm -rf "$CASE_ROOT"
}
trap cleanup EXIT

createdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$SOURCE_DB"; SOURCE_CREATED=true
createdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$TARGET_DB"; TARGET_CREATED=true
psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$SOURCE_DB" -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE synthetic_restore_probe(id integer PRIMARY KEY, label text NOT NULL);
INSERT INTO synthetic_restore_probe VALUES (1, 'alpha'), (2, 'beta');
SQL
psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$TARGET_DB" -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE sentinel(id integer PRIMARY KEY);
INSERT INTO sentinel VALUES (7);
SQL

mkdir -p "$CASE_ROOT/original" "$CASE_ROOT/moved" "$CASE_ROOT/other-cwd"
DB_HOST="$SOCKET" DB_PORT="$PORT" DB_USER="$USER_NAME" DB_NAME="$SOURCE_DB" \
 DB_PASSWORD=synthetic-local-placeholder BACKUP_DIR="$CASE_ROOT/original" \
 "$ROOT/scripts/backup_db.sh"
ARCHIVE=$(find "$CASE_ROOT/original" -name 'jobs_backup_*.sql.gz' -type f -print -quit)
mv "$ARCHIVE" "$ARCHIVE.sha256" "$CASE_ROOT/moved/"
MOVED="$CASE_ROOT/moved/$(basename "$ARCHIVE")"
SIDECAR="$MOVED.sha256"
SIDECAR_RECORD=$(cat "$SIDECAR")

(
 cd "$CASE_ROOT/other-cwd"
 DB_HOST="$SOCKET" DB_PORT="$PORT" DB_USER="$USER_NAME" DB_NAME="$TARGET_DB" \
  DB_PASSWORD=synthetic-local-placeholder "$ROOT/scripts/restore_db.sh" "$MOVED" --force
)
RESTORED=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$TARGET_DB" -Atqc \
 "SELECT string_agg(id::text || ':' || label, ',' ORDER BY id) FROM synthetic_restore_probe")

# Valid-checksum archive with a SQL error must fail atomically and omit success.
cat > "$CASE_ROOT/bad.sql" <<'SQL'
CREATE TABLE should_rollback(id integer);
THIS IS INVALID SQL;
INSERT INTO should_rollback VALUES (1);
SQL
gzip -9 -c "$CASE_ROOT/bad.sql" > "$CASE_ROOT/bad.sql.gz"
(cd "$CASE_ROOT" && shasum -a 256 bad.sql.gz > bad.sql.gz.sha256)
set +e
BAD_OUTPUT=$(DB_HOST="$SOCKET" DB_PORT="$PORT" DB_USER="$USER_NAME" DB_NAME="$TARGET_DB" \
 DB_PASSWORD=synthetic-local-placeholder "$ROOT/scripts/restore_db.sh" "$CASE_ROOT/bad.sql.gz" --force 2>&1)
BAD_EXIT=$?
set -e
BAD_TABLE=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$TARGET_DB" -Atqc \
 "SELECT COALESCE(to_regclass('public.should_rollback')::text, 'ABSENT')")
BAD_SUCCESS_COUNT=$(printf '%s' "$BAD_OUTPUT" | grep -c 'Database restore completed successfully' || true)

# Each invalid sidecar protects the DB before the archive can insert sentinel 99.
printf 'INSERT INTO sentinel VALUES (99);\n' | gzip -9 > "$CASE_ROOT/would_mutate.sql.gz"
ACTUAL=$(shasum -a 256 "$CASE_ROOT/would_mutate.sql.gz" | awk '{print $1}')

run_sidecar_case() {
  local kind=$1
  local content=$2
  printf '%s' "$content" > "$CASE_ROOT/would_mutate.sql.gz.sha256"
  set +e
  DB_HOST="$SOCKET" DB_PORT="$PORT" DB_USER="$USER_NAME" DB_NAME="$TARGET_DB" \
   DB_PASSWORD=synthetic-local-placeholder "$ROOT/scripts/restore_db.sh" \
   "$CASE_ROOT/would_mutate.sql.gz" --force >"$CASE_ROOT/$kind.out" 2>&1
  local status=$?
  set -e
  local sentinel_count
  sentinel_count=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$TARGET_DB" -Atqc \
   "SELECT count(*) FROM sentinel WHERE id=99")
  echo "${kind}_EXIT=$status ${kind}_SENTINEL99=$sentinel_count"
  [[ "$status" -ne 0 && "$sentinel_count" == 0 ]]
}

CORRUPT=$(printf '0%.0s' {1..64})
run_sidecar_case corrupt "$CORRUPT  would_mutate.sql.gz
"
run_sidecar_case malformed "not-a-digest  would_mutate.sql.gz
"
run_sidecar_case multirecord "$ACTUAL  would_mutate.sql.gz
$ACTUAL  second.sql.gz
"

echo "SOURCE_SHA=$(git -C "$ROOT" rev-parse HEAD)"
echo "DIFF_SHA256=$(git -C "$ROOT" diff -- scripts/backup_db.sh scripts/restore_db.sh docs/RECOVERY.md | shasum -a 256 | awk '{print $1}')"
echo "SIDECAR_RECORD=$SIDECAR_RECORD"
echo "RESTORED_ROWS=$RESTORED"
echo "SQL_ERROR_EXIT=$BAD_EXIT SQL_ERROR_TABLE=$BAD_TABLE SQL_ERROR_SUCCESS_COUNT=$BAD_SUCCESS_COUNT"
printf 'SQL_ERROR_OUTPUT_BEGIN\n%s\nSQL_ERROR_OUTPUT_END\n' "$BAD_OUTPUT"

[[ "$RESTORED" == "1:alpha,2:beta" ]]
[[ "$BAD_EXIT" -ne 0 && "$BAD_TABLE" == "ABSENT" && "$BAD_SUCCESS_COUNT" == 0 ]]

dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$SOURCE_DB"; SOURCE_CREATED=false
dropdb -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$TARGET_DB"; TARGET_CREATED=false
SOURCE_LEFT=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d postgres -Atqc \
 "SELECT count(*) FROM pg_database WHERE datname='$SOURCE_DB'")
TARGET_LEFT=$(psql -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d postgres -Atqc \
 "SELECT count(*) FROM pg_database WHERE datname='$TARGET_DB'")
echo "CLEANUP_SOURCE_COUNT=$SOURCE_LEFT CLEANUP_TARGET_COUNT=$TARGET_LEFT"
[[ "$SOURCE_LEFT" == 0 && "$TARGET_LEFT" == 0 ]]
