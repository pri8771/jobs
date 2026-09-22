# Disaster Recovery & Operations Runbook

This document defines the emergency procedures, backup protocols, and disaster recovery runbooks for Jobs Automation OS.

---

## 1. System Architecture & State Boundaries

The Jobs Automation OS consists of:
- **Relational State Store**: PostgreSQL 16 (storing companies, jobs, sources, evaluations, applications, events, contacts, interviews, tasks, and audit logs).
- **Candidate Ground Truth**: Local YAML configuration files (`config/candidate_profile.yaml`, `config/policy_registry.yaml`, `config/job_search.yaml`).
- **Audit Trails**: SHA-256 hashed application packets and provider message linking (`InboundMessageModel`, `AuditLogModel`).
- **Runtime Engines**:
  - `jobs-dashboard`: HTTP server and REST API (`http://localhost:8080`).
  - `jobs-worker`: Scheduled background daemon executing periodic sweeps (4-hour intervals).

---

## 2. Emergency Incident Response: Kill Switches

If anomalous behavior, unexpected ATS rejections, or platform terms changes occur:

### 2.1 Activate Global Kill Switch
To immediately halt all automated applications across every platform:
```bash
# Option A: Environment Variable (persists across restarts)
export JOBS_AUTOMATION_KILL_SWITCH=true

# Option B: In Docker Compose
# Add JOBS_AUTOMATION_KILL_SWITCH: "true" to docker-compose.yml and restart worker
docker compose restart jobs-worker
```
When active:
- All automated ATS adapters instantly reject submission attempts (`AUTOMATION_KILLED`).
- Applications remain safely in `PREPARED` or route to `NEEDS_REVIEW`.
- No outbound HTTP submissions or form modifications occur.

### 2.2 Activate Per-Platform Kill Switch
To halt submissions for a specific platform (e.g. Greenhouse or Lever) while leaving other adapters running:
```bash
export JOBS_AUTOMATION_KILL_SWITCH_GREENHOUSE=true
# or
export JOBS_AUTOMATION_KILL_SWITCH_LEVER=true
```

---

## 3. Database Backup & Retention Policy

### 3.1 Automated Backups
Run the backup script directly or schedule it via cron:
```bash
./scripts/backup_db.sh
```
What it does:
1. Executes `pg_dump` with `--clean --if-exists --no-owner`.
2. Compresses the dump with `gzip -9` to `backups/jobs_backup_<TIMESTAMP>.sql.gz`.
3. Computes a SHA-256 verification hash stored at `<BACKUP_FILE>.sha256`.
4. Automatically retains backups for 14 days, pruning older files.

### 3.2 Backup Verification
Verify backup archive integrity:
```bash
(cd backups && shasum -a 256 -c jobs_backup_20260920_140000Z.sql.gz.sha256)
```

---

## 4. Cold-Start Database Restore Runbook

In the event of database volume loss, data corruption, or hardware migration:

### 4.1 Step 1: Ensure Target Database is Reachable
```bash
docker compose up -d postgres
pg_isready -h localhost -p 5433 -U jobs
```

### 4.2 Step 2: Restore from Gzip Backup
```bash
./scripts/restore_db.sh backups/jobs_backup_20260920_140000Z.sql.gz --force
```
The script will:
- Verify the supplied archive against its SHA-256 sidecar, even after the pair
  has moved to another directory or host. Older path-bearing sidecars remain supported.
- Terminate existing database connections.
- Execute the restore in a single transaction and fail on the first SQL error.
  A SQL error rolls back the transaction, returns a nonzero exit, and never
  prints the successful completion message.

### 4.3 Step 3: Run Database Migrations
```bash
alembic upgrade head
```

### 4.4 Step 4: Verify System Health
```bash
jobs-automation health-check
```

---

## 5. State Reconciliation from Raw Email Feeds

Because email messages serve as immutable evidence, if a catastrophic database failure occurs without a recent backup:
1. Initialize a clean database (`alembic upgrade head`).
2. Run ingestion sweep across Gmail archive:
   ```bash
   jobs-automation ingest-emails --full-history
   ```
3. Run lifecycle reconciliation:
   ```bash
   jobs-automation update-lifecycle
   ```
This rebuilds discovered jobs, companies, touchpoints, and recruiter contacts directly from raw cryptographic message headers and bodies.

---

## 6. System Health Diagnostic Checklist

Run `jobs-automation health-check` periodically to monitor:
- **Database Latency**: Query execution under 500ms.
- **Queue Backlog**: Pending review tasks (`TaskModel`) requiring candidate input.
- **Kill-Switch Readiness**: Active global and adapter flags.
- **Policy Registry Freshness**: Detect any platforms whose 90-day review period (`review_due_at`) has elapsed.
- **ATS Adapter Registry**: Verify all supported domains (`greenhouse.io`, `lever.co`) are loaded.
