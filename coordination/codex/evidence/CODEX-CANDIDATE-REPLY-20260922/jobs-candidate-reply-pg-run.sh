#!/usr/bin/env bash
set -Eeuo pipefail

expected_sha="${1:?usage: $0 EXPECTED_SOURCE_SHA [SOURCE_DIR]}"
source_dir="${2:-/Users/pchordia/Downloads/swarm_codex/review/jobs-fixture-source}"
socket_dir="${JOBS_PG_SOCKET:-/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd}"
pg_port="${JOBS_PG_PORT:-56422}"
pg_user="${JOBS_PG_USER:-$(id -un)}"
venv_dir="${JOBS_VENV_DIR:-/Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
short_sha="${expected_sha:0:12}"
db_name="jobs_candidate_reply_${$}_$(date +%s)"
log="/tmp/jobs-candidate-reply-pg-${short_sha}-${stamp}.log"
database_url="postgresql+psycopg://${pg_user}@/${db_name}?host=${socket_dir}&port=${pg_port}"

cleanup() {
  local original_rc=$?
  set +e
  dropdb -h "$socket_dir" -p "$pg_port" -U "$pg_user" --if-exists "$db_name" >>"$log" 2>&1
  local drop_rc=$?
  local remaining
  remaining="$(psql -h "$socket_dir" -p "$pg_port" -U "$pg_user" -d postgres -Atqc \
    "select count(*) from pg_database where datname = '$db_name';" 2>>"$log")"
  local count_rc=$?
  printf 'cleanup_drop_exit=%s\ncleanup_query_exit=%s\ncleanup_database_count=%s\n' \
    "$drop_rc" "$count_rc" "${remaining:-QUERY_FAILED}" >>"$log"
  if [[ $original_rc -eq 0 && ( $drop_rc -ne 0 || $count_rc -ne 0 || "$remaining" != "0" ) ]]; then
    original_rc=90
  fi
  printf 'final_exit=%s\n' "$original_rc" >>"$log"
  printf 'evidence_log=%s\n' "$log"
  exit "$original_rc"
}
trap cleanup EXIT

: >"$log"
if [[ ! -f /tmp/jobs-candidate-reply-pg.py ]]; then
  printf 'ERROR: missing /tmp/jobs-candidate-reply-pg.py\n' | tee -a "$log" >&2
  exit 2
fi
if [[ ! -x "$venv_dir/bin/alembic" || ! -x "$venv_dir/bin/python" ]]; then
  printf 'ERROR: required virtualenv executables unavailable at %s\n' "$venv_dir" | tee -a "$log" >&2
  exit 2
fi

actual_sha="$(git -C "$source_dir" rev-parse HEAD)"
if [[ "$actual_sha" != "$expected_sha" ]]; then
  printf 'ERROR: source HEAD %s does not equal expected %s\n' "$actual_sha" "$expected_sha" | tee -a "$log" >&2
  exit 3
fi
if ! git -C "$source_dir" diff --quiet -- src; then
  printf 'ERROR: source tree has uncommitted production changes\n' | tee -a "$log" >&2
  exit 4
fi

printf 'source_sha=%s\nsource_state=exact_committed_source\nsource_dir=%s\n' \
  "$actual_sha" "$source_dir" >>"$log"
printf 'scenario=synthetic partial seeded job/application; not golden or live proof\n' >>"$log"
printf 'stage_preservation_baseline=post-inbound SCREENING\n' >>"$log"
printf 'database=%s socket=%s port=%s user=%s\n' \
  "$db_name" "$socket_dir" "$pg_port" "$pg_user" >>"$log"
printf 'harness_sha256=%s\n' "$(shasum -a 256 /tmp/jobs-candidate-reply-pg.py | cut -d' ' -f1)" >>"$log"

createdb -h "$socket_dir" -p "$pg_port" -U "$pg_user" "$db_name" >>"$log" 2>&1
printf 'createdb_exit=0\n' >>"$log"

(
  cd "$source_dir"
  DATABASE_URL="$database_url" PYTHONPATH="$source_dir/src:$source_dir" \
    "$venv_dir/bin/alembic" upgrade head
) >>"$log" 2>&1
printf 'alembic_upgrade_head_exit=0\n' >>"$log"

JOBS_REPLY_DB="$db_name" \
JOBS_PG_SOCKET="$socket_dir" \
JOBS_PG_PORT="$pg_port" \
JOBS_PG_USER="$pg_user" \
SOURCE_BASE_SHA="$actual_sha" \
SOURCE_DIFF_SHA256="committed-tree" \
PYTHONPATH="$source_dir/src:$source_dir" \
  "$venv_dir/bin/python" /tmp/jobs-candidate-reply-pg.py >>"$log" 2>&1
printf 'harness_exit=0\n' >>"$log"
