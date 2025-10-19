# Runbook: Database Migration Operations

This runbook covers safe database migration procedures for the Brownie Metadata Database.

## TL;DR
- Always backup before migrations
- Test migrations in staging first
- Use zero-downtime migration patterns
- Monitor during and after migration

---

## 1) Pre-Migration Checklist

### Backup Verification
```bash
# Verify latest backup exists and is valid
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
backups = manager.list_backups()
print(f'Latest backup: {backups[0] if backups else \"None\"}')
"
```

### Health Check
```bash
# Check database health
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.database.connection import get_db_engine
engine = get_db_engine()
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection: OK')
"
```

### Resource Check
```bash
# Check available disk space
kubectl exec -n brownie-metadata deployment/postgres-primary -- df -h /var/lib/postgresql/data

# Check memory usage
kubectl top pods -n brownie-metadata
```

---

## 2) Migration Types

### Schema Changes (Additive)
```bash
# 1. Create migration
alembic revision --autogenerate -m "add new_table"

# 2. Review generated migration
cat alembic/versions/*_add_new_table.py

# 3. Test locally
docker-compose up -d postgres
alembic upgrade head
make test

# 4. Apply to staging
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic upgrade head

# 5. Apply to production
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic upgrade head
```

### Data Migrations
```bash
# 1. Create data migration
alembic revision -m "migrate_user_data"

# 2. Edit migration file to include data transformation
# Example: backfill missing data, transform existing data

# 3. Test with small dataset first
# 4. Run in chunks for large datasets
# 5. Monitor performance during migration
```

### Index Operations
```bash
# For large tables, use CONCURRENTLY
# Edit migration file:
# CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

# Monitor index creation
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE indexname = 'idx_users_email';
"
```

---

## 3) Zero-Downtime Migration Patterns

### Add Column Pattern
```sql
-- Step 1: Add nullable column
ALTER TABLE users ADD COLUMN new_field TEXT;

-- Step 2: Backfill data (in chunks)
UPDATE users SET new_field = 'default_value' WHERE new_field IS NULL;

-- Step 3: Add NOT NULL constraint (if needed)
ALTER TABLE users ALTER COLUMN new_field SET NOT NULL;
```

### Rename Column Pattern
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN new_name TEXT;

-- Step 2: Dual-write (application code)
-- Step 3: Backfill data
UPDATE users SET new_name = old_name WHERE new_name IS NULL;

-- Step 4: Switch reads to new column
-- Step 5: Drop old column
ALTER TABLE users DROP COLUMN old_name;
```

---

## 4) Migration Monitoring

### During Migration
```bash
# Monitor migration progress
kubectl logs -f -n brownie-metadata deployment/brownie-metadata-app

# Check for locks
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT pid, state, query_start, query 
FROM pg_stat_activity 
WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%';
"

# Monitor disk usage
kubectl exec -n brownie-metadata deployment/postgres-primary -- df -h
```

### Post-Migration Verification
```bash
# Verify migration applied
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic current

# Check table structure
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "\d users"

# Run application tests
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -m pytest tests/

# Check application health
curl http://localhost:8000/health
```

---

## 5) Rollback Procedures

### Schema Rollback
```bash
# Rollback one migration
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic downgrade -1

# Rollback to specific revision
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic downgrade <revision_id>

# Verify rollback
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- alembic current
```

### Data Rollback
```bash
# If data was corrupted, restore from backup
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
manager.restore_backup('backup_name')
"
```

---

## 6) Emergency Procedures

### Migration Stuck
```bash
# Check for long-running queries
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"

# Kill stuck query (if safe)
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT pg_terminate_backend(<pid>);
"
```

### Database Lock
```bash
# Check for locks
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
"
```

---

## 7) Commands Reference

```bash
# Migration commands
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history --verbose

# Database connection
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -U brownie -d brownie_metadata

# Application logs
kubectl logs -f -n brownie-metadata deployment/brownie-metadata-app

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

---

## 8) Definition of Done

- [ ] Migration tested in staging environment
- [ ] Backup created and verified
- [ ] Migration applied successfully
- [ ] Application health checks pass
- [ ] Performance metrics within normal range
- [ ] Rollback plan documented and tested
- [ ] Team notified of changes
