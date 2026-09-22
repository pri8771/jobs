#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT=/Users/pchordia/Downloads/swarm_codex/review/jobs-gmail-source
CASE_ROOT=$(mktemp -d /tmp/jobs-v20-restore-cwd.XXXXXX)
trap 'rm -rf "$CASE_ROOT"' EXIT

mkdir -p "$CASE_ROOT/original/backups" "$CASE_ROOT/invocation"
printf '%s\n' 'synthetic SQL dump; no database connection' | gzip -9 \
  > "$CASE_ROOT/original/backups/jobs_backup_synthetic.sql.gz"

# Reproduce backup_db.sh's checksum shape: BACKUP_FILE is a relative path, so
# the sidecar records that relative path rather than only the archive basename.
(
  cd "$CASE_ROOT/original"
  shasum -a 256 backups/jobs_backup_synthetic.sql.gz \
    > backups/jobs_backup_synthetic.sql.gz.sha256
)

ARCHIVE="$CASE_ROOT/original/backups/jobs_backup_synthetic.sql.gz"
SIDECAR="$ARCHIVE.sha256"

echo "SOURCE_SHA=$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
echo "SCRIPT_SHA256=$(shasum -a 256 "$SOURCE_ROOT/scripts/restore_db.sh" | awk '{print $1}')"
echo "ARCHIVE=$ARCHIVE"
echo "SIDECAR_CONTENT=$(cat "$SIDECAR")"
echo "DIRECT_HASH=$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"

set +e
(
  cd "$CASE_ROOT/invocation"
  "$SOURCE_ROOT/scripts/restore_db.sh" "$ARCHIVE" --force
)
STATUS=$?
set -e

echo "RESTORE_EXIT=$STATUS"
if [[ "$STATUS" -eq 0 ]]; then
  echo "UNEXPECTED: restore reached database stage"
  exit 90
fi

# Confirm this was a checksum-path failure before credentials or DB access.
echo "OBSERVED=valid archive and matching sidecar fail verification when invoked outside checksum-recording cwd"
exit 0
