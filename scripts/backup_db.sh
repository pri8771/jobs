#!/usr/bin/env bash
# Jobs Automation Database Backup Script
# Creates timestamped, gzip-compressed PostgreSQL database dump with SHA-256 verification.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-backups}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/jobs_backup_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-jobs}"
DB_NAME="${DB_NAME:-jobs}"
export PGPASSWORD="${DB_PASSWORD:-jobs}"

echo "=========================================================="
echo "Jobs Automation OS — Database Backup Utility"
echo "Target DB: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "Destination: ${BACKUP_FILE}"
echo "=========================================================="

echo "Dumping PostgreSQL schema and data..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
  --clean --if-exists --no-owner --no-privileges | gzip -9 > "${BACKUP_FILE}"

echo "Generating SHA-256 integrity checksum..."
shasum -a 256 "${BACKUP_FILE}" > "${CHECKSUM_FILE}"

BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
echo "Backup successfully created: ${BACKUP_FILE} (${BACKUP_SIZE})"
echo "SHA-256 Checksum: $(cat "${CHECKSUM_FILE}")"

# Retention: keep last 14 backups
echo "Pruning backups older than 14 days..."
find "${BACKUP_DIR}" -name "jobs_backup_*.sql.gz" -mtime +14 -delete || true
find "${BACKUP_DIR}" -name "jobs_backup_*.sql.gz.sha256" -mtime +14 -delete || true

echo "Backup workflow completed successfully."
