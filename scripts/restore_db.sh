#!/usr/bin/env bash
# Jobs Automation Database Restore Script
# Restores PostgreSQL database from a gzip-compressed backup after verifying SHA-256 integrity.

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <path-to-backup.sql.gz> [--force]"
  exit 1
fi

BACKUP_FILE="$1"
FORCE="${2:-}"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Error: Backup file '${BACKUP_FILE}' does not exist."
  exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
  echo "Verifying SHA-256 integrity checksum..."
  shasum -a 256 -c "${CHECKSUM_FILE}"
else
  if [ "${FORCE}" = "--skip-checksum-emergency-override" ] || [ "${3:-}" = "--skip-checksum-emergency-override" ]; then
    echo "AUDIT WARNING: Emergency checksum override activated. Restoring without SHA-256 verification."
  else
    echo "Error: Checksum file '${CHECKSUM_FILE}' is missing. Restore failed closed to prevent corruption."
    echo "To override in an emergency, specify --skip-checksum-emergency-override."
    exit 1
  fi
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-jobs}"
DB_NAME="${DB_NAME:-jobs}"

if [ -z "${DB_PASSWORD:-}" ]; then
  if [ "${ALLOW_DEFAULT_DEV_CREDENTIALS:-false}" = "true" ]; then
    export PGPASSWORD="jobs"
  else
    echo "Error: DB_PASSWORD must be set in environment (or set ALLOW_DEFAULT_DEV_CREDENTIALS=true for local dev)."
    exit 1
  fi
else
  export PGPASSWORD="${DB_PASSWORD}"
fi

echo "=========================================================="
echo "Jobs Automation OS — Database Restore Utility"
echo "Target DB: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "Source: ${BACKUP_FILE}"
echo "=========================================================="

if [ "${FORCE}" != "--force" ]; then
  read -p "WARNING: This will overwrite existing data in '${DB_NAME}'. Continue? (y/N): " -r CONFIRM
  if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    echo "Restore aborted by user."
    exit 0
  fi
fi

echo "Terminating existing database connections..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true

echo "Restoring database from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --single-transaction

echo "Database restore completed successfully."
