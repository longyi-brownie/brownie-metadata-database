## Runbook: Coordinating Database Schema Changes with the Metadata API

This runbook defines a safe, zero-downtime process to make database schema changes in `brownie-metadata-database` while keeping `brownie-metadata-api` working smoothly.

### TL;DR
- Prefer additive, backward-compatible DB changes first (expand).
- Deploy DB migration → then deploy API change that starts using it.
- After the fleet runs on the new path, do a separate cleanup (contract) migration.

---

## 1) Change Taxonomy
- Additive (safe): new tables/columns/indexes; columns nullable with sensible defaults; enum value additions.
- Contract (risky): drop/rename columns; make columns NOT NULL; tighten constraints; remove enum values.
- Data migration: backfills and transformations needed to populate new structures.

Rule of thumb: You can deploy additive changes before the API change; you must deploy contract changes after the API no longer depends on the old shape.

---

## 2) Golden Workflow (Expand → Migrate → Contract)

### Expand (DB-first, backward compatible)
1. Design an additive migration (no breaking changes).
2. Create migration:
   ```bash
   cd brownie-metadata-database
   alembic revision --autogenerate -m "<expand: add X>"
   alembic upgrade head
   ```
3. Verify locally:
   ```bash
   make test
   make test-integration
   ```

### Update API (consume new schema)
4. Implement API changes in `brownie-metadata-api` to read/write the new fields while remaining tolerant of old data.
5. Test API locally against a DB at migration head:
   ```bash
   cd ../brownie-metadata-api
   make test
   docker-compose up -d
   curl :8080/health
   ```

### Contract (cleanup once stable)
6. After the new API is fully deployed and traffic is confirmed healthy, plan cleanup:
   - Backfill/finalize data if needed.
   - Remove dual-writes/feature flags in API.
   - Create a contract migration to drop old columns/indexes/constraints.
7. Create & apply contract migration:
   ```bash
   cd ../brownie-metadata-database
   alembic revision --autogenerate -m "<contract: drop old Y>"
   alembic upgrade head
   ```

---

## 3) Environment-by-Environment Flow

### Local
```bash
# In DB repo
alembic revision --autogenerate -m "<desc>"
alembic upgrade head
make test
make test-integration

# In API repo
make test
docker-compose up -d
```

### CI
- DB repo CI:
  - Unit tests
  - Apply migrations on ephemeral Postgres
  - Integration tests (verifies API can import models, connect, query, and create records)
- API repo CI:
  - Unit/Integration tests against ephemeral Postgres at DB head

### Staging → Production (Zero-Downtime)
1. Apply DB migration (expand) in staging/prod.
2. Deploy API that uses the new shape (still backward compatible).
3. Observe metrics/logs/errors.
4. If needed, run backfill job.
5. Later, apply DB contract migration; deploy API cleanup (remove dual-writes/flags).

Rollback guidance:
- If API fails after expand: rollback API (DB is a superset; safe).
- If contract migration breaks something: `alembic downgrade -1` and restore API path.

---

## 4) Patterns and Caveats
- Renames: avoid direct renames. Add new column, dual-write, backfill, flip reads, later drop old.
- NOT NULL: add column nullable; backfill; then add NOT NULL constraint in a later migration.
- Enums (Postgres): add new enum values via `ALTER TYPE` before the API might emit them.
- Indexes: prefer concurrent creation in raw SQL if needed; avoid long locks.
- Foreign keys: add after backfill or deferrable when large tables are involved.
- Large backfills: chunk by ID ranges, throttle, monitor.
- Optimistic concurrency: continue to honor `version` columns and If-Match semantics.
- RBAC changes: gate behind feature flag; monitor denied requests before enforcing.

---

## 5) Integration Checks (What to Verify)
Run in DB repo:
```bash
make test-integration
```
This verifies:
- Migrations apply successfully to a clean database.
- API can import DB models.
- API connects to DB and queries major tables.
- API can create representative records.
- Tables and indexes expected by API exist.

---

## 6) Example: Column Rename with Dual-Write

Goal: rename `users.fullname` → `users.full_name` without downtime.

1) Expand migration (DB):
```sql
-- Add new column, nullable
ALTER TABLE users ADD COLUMN full_name TEXT NULL;
```
Alembic:
```bash
alembic revision --autogenerate -m "expand: add users.full_name"
alembic upgrade head
```

2) API change:
- Start writing both `fullname` and `full_name`.
- Read priority: prefer `full_name`, fallback to `fullname`.
- Backfill job: copy `fullname` → `full_name` for historical rows (chunked, monitored).

3) Contract migration (DB):
```sql
-- After backfill and code cutover
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;  -- if desired
ALTER TABLE users DROP COLUMN fullname;
```
Alembic:
```bash
alembic revision --autogenerate -m "contract: drop users.fullname"
alembic upgrade head
```

---

## 7) Commands Cheat Sheet
```bash
# Create migration from model changes
alembic revision --autogenerate -m "<desc>"

# Apply latest migration
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# See current revision
alembic current

# See history
alembic history --verbose

# Run DB integration tests
make test-integration
```

---

## 8) Definition of Done for Schema Changes
- [ ] Additive migration merged and applied.
- [ ] API updated to use new shape, with backward compatibility.
- [ ] Integration tests pass locally and in CI.
- [ ] Staging deploy green; metrics/logs clean.
- [ ] (If needed) Backfill completed and verified.
- [ ] Contract migration applied; API cleanup deployed.


