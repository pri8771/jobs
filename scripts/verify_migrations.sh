#!/usr/bin/env bash
# Verify the Alembic migration chain against a real PostgreSQL database.
# Intended for CI and local integration verification.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set for migration verification}"

echo "== Alembic migration verification =="
echo "Database URL is configured (value intentionally not printed)."

echo "1/5: Ensure database starts from base revision"
alembic downgrade base >/dev/null 2>&1 || true

echo "2/5: Upgrade empty database to head"
alembic upgrade head

CURRENT="$(alembic current | tail -n 1)"
echo "Current revision after upgrade: ${CURRENT}"

echo "3/5: Downgrade one revision from head"
alembic downgrade -1

DOWNGRADED="$(alembic current | tail -n 1)"
echo "Current revision after downgrade: ${DOWNGRADED}"

echo "4/5: Re-upgrade to head"
alembic upgrade head

FINAL="$(alembic current | tail -n 1)"
echo "Current revision after re-upgrade: ${FINAL}"

echo "5/5: Verify head revision is applied"
HEADS="$(alembic heads)"
HEAD_REV="$(printf '%s\n' "${HEADS}" | awk '{print $1}' | head -n 1)"
if ! printf '%s' "${FINAL}" | grep -q "${HEAD_REV}"; then
  echo "ERROR: expected final revision to contain head ${HEAD_REV}, got: ${FINAL}" >&2
  exit 1
fi

echo "Migration verification passed."
