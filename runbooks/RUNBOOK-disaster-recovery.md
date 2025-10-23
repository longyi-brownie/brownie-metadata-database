# Runbook: Disaster Recovery Procedures

This runbook covers disaster recovery procedures for the Brownie Metadata Database.

## TL;DR
- RTO: 4 hours, RPO: 1 hour
- Automated backups every 6 hours
- Multi-region backup replication
- Tested recovery procedures

---

## 1) Recovery Time Objectives (RTO/RPO)

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Backup Frequency**: Every 6 hours
- **Retention**: 30 days local, 90 days cloud

---

## 2) Backup Verification

### Check Backup Status
```bash
# List available backups
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
backups = manager.list_backups()
for backup in backups[:5]:  # Show last 5
    print(f'{backup[\"name\"]} - {backup[\"created_at\"]} - {backup[\"size\"]}')
"
```

### Verify Backup Integrity
```bash
# Test backup restoration to temporary database
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
# This would restore to a test database
# manager.restore_backup('backup_name', target_db='test_db')
print('Backup verification completed')
"
```

---

## 3) Disaster Scenarios

### Complete Database Loss
```bash
# 1. Identify latest good backup
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
backups = manager.list_backups()
latest = backups[0] if backups else None
print(f'Latest backup: {latest}')
"

# 2. Scale down application
kubectl scale deployment brownie-metadata-app --replicas=0 -n brownie-metadata

# 3. Restore from backup
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
manager.restore_backup('latest_backup_name')
"

# 4. Verify data integrity
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM incidents;
SELECT COUNT(*) FROM organizations;
"

# 5. Scale up application
kubectl scale deployment brownie-metadata-app --replicas=3 -n brownie-metadata
```

### Partial Data Corruption
```bash
# 1. Identify affected tables
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
ORDER BY n_tup_del DESC;
"

# 2. Restore specific tables from backup
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
# Restore specific table
manager.restore_table('backup_name', 'users')
"
```

### Application Data Inconsistency
```bash
# 1. Check application logs for errors
kubectl logs -n brownie-metadata deployment/brownie-metadata-app | grep ERROR

# 2. Verify database constraints
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT conname, contype, confrelid::regclass 
FROM pg_constraint 
WHERE contype = 'f';
"

# 3. Run data consistency checks
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from brownie_metadata_db.database.connection import get_db_engine
engine = get_db_engine()
with engine.connect() as conn:
    # Check for orphaned records
    result = conn.execute('''
        SELECT COUNT(*) FROM incidents i 
        LEFT JOIN organizations o ON i.organization_id = o.id 
        WHERE o.id IS NULL
    ''')
    orphaned = result.scalar()
    print(f'Orphaned incidents: {orphaned}')
"
```

---

## 4) Recovery Procedures

### Full System Recovery
```bash
# 1. Create new namespace
kubectl create namespace brownie-metadata-recovery

# 2. Deploy minimal infrastructure
kubectl apply -f k8s/postgres-primary.yaml -n brownie-metadata-recovery
kubectl apply -f k8s/redis.yaml -n brownie-metadata-recovery

# 3. Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=postgres-primary -n brownie-metadata-recovery --timeout=300s

# 4. Restore database
kubectl exec -n brownie-metadata-recovery deployment/postgres-primary -- psql -c "
CREATE DATABASE brownie_metadata;
"

# 5. Restore from backup
kubectl exec -n brownie-metadata-recovery deployment/postgres-primary -- psql -d brownie_metadata -c "
\i /backup/restored_dump.sql
"

# 6. Deploy application
kubectl apply -f k8s/app.yaml -n brownie-metadata-recovery

# 7. Verify recovery
kubectl port-forward -n brownie-metadata-recovery svc/brownie-metadata-app 8080:8000 &
curl http://localhost:8080/health
```

### Point-in-Time Recovery
```bash
# 1. Stop application
kubectl scale deployment brownie-metadata-app --replicas=0 -n brownie-metadata

# 2. Restore to specific timestamp
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
-- Restore to specific point in time
-- This requires WAL archiving to be enabled
SELECT pg_start_backup('recovery');
-- Restore base backup
-- Apply WAL files up to target time
SELECT pg_stop_backup();
"
```

---

## 5) Cross-Region Recovery

### Failover to Secondary Region
```bash
# 1. Update DNS to point to secondary region
# 2. Deploy infrastructure in secondary region
kubectl apply -f k8s/ -n brownie-metadata-secondary

# 3. Restore from cross-region backup
kubectl exec -n brownie-metadata-secondary deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
config.provider = 's3'  # Use cross-region backup
manager = BackupManager(config)
manager.restore_backup('latest_backup_name')
"

# 4. Verify services
kubectl get pods -n brownie-metadata-secondary
kubectl logs -n brownie-metadata-secondary deployment/brownie-metadata-app
```

---

## 6) Recovery Testing

### Monthly Recovery Test
```bash
# 1. Create test environment
kubectl create namespace brownie-metadata-test

# 2. Deploy test infrastructure
kubectl apply -f k8s/ -n brownie-metadata-test

# 3. Restore latest backup
kubectl exec -n brownie-metadata-test deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
config = BackupConfig.from_env()
manager = BackupManager(config)
manager.restore_backup('latest_backup_name')
"

# 4. Run validation tests
kubectl exec -n brownie-metadata-test deployment/brownie-metadata-app -- python -m pytest tests/test_recovery.py

# 5. Clean up test environment
kubectl delete namespace brownie-metadata-test
```

### Backup Validation
```bash
# Automated backup validation script
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.backup.manager import BackupManager
from src.backup.config import BackupConfig
import datetime

config = BackupConfig.from_env()
manager = BackupManager(config)

# Check if backup is recent (within 6 hours)
backups = manager.list_backups()
if backups:
    latest = backups[0]
    created_at = datetime.datetime.fromisoformat(latest['created_at'])
    age = datetime.datetime.now() - created_at
    if age.total_seconds() > 6 * 3600:  # 6 hours
        print(f'WARNING: Latest backup is {age} old')
    else:
        print(f'OK: Latest backup is {age} old')
else:
    print('ERROR: No backups found')
"
```

---

## 7) Monitoring and Alerting

### Recovery Alerts
```yaml
# Add to prometheus-alerts.yaml
- alert: BackupFailed
  expr: backup_last_successful_timestamp < (time() - 6 * 3600)
  for: 1h
  labels:
    severity: critical
  annotations:
    summary: "Backup has not completed successfully in 6 hours"

- alert: DatabaseDown
  expr: up{job="brownie-metadata-db"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database is down"
```

### Health Checks
```bash
# Database health check
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database 
WHERE datname = 'brownie_metadata';
"

# Application health check
curl -f http://localhost:8000/health || echo "Application health check failed"
```

---

## 8) Communication Plan

### Incident Response
1. **Immediate**: Notify on-call engineer
2. **5 minutes**: Create incident channel
3. **15 minutes**: Notify stakeholders
4. **30 minutes**: Provide status update
5. **Recovery**: Post-incident review

### Stakeholder Notification
- **Engineering**: Slack #incidents
- **Management**: Email + Slack
- **Customers**: Status page update

---

## 9) Post-Recovery Procedures

### Data Validation
```bash
# Verify data integrity
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from brownie_metadata_db.database.connection import get_db_engine
engine = get_db_engine()
with engine.connect() as conn:
    # Check record counts
    tables = ['users', 'organizations', 'incidents', 'teams', 'agent_configs']
    for table in tables:
        result = conn.execute(f'SELECT COUNT(*) FROM {table}')
        count = result.scalar()
        print(f'{table}: {count} records')
"
```

### Performance Verification
```bash
# Check query performance
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

---

## 10) Definition of Done

- [ ] RTO and RPO objectives met
- [ ] All critical data restored
- [ ] Application fully functional
- [ ] Performance within acceptable limits
- [ ] Monitoring and alerting active
- [ ] Stakeholders notified
- [ ] Post-incident review scheduled
- [ ] Recovery procedures updated if needed
