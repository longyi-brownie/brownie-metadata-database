# Backup System Documentation

The Brownie Metadata Database includes a comprehensive, enterprise-ready backup system that works out of the box with minimal configuration.

## 🚀 Quick Start

### 1. Configure Backup Settings

Set environment variables for your backup provider:

```bash
# Basic configuration
export BACKUP_PROVIDER="s3"  # s3, gcs, azure, local
export BACKUP_DESTINATION="my-backup-bucket/database"
export BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
export BACKUP_RETENTION_DAYS="30"

# Cloud provider credentials
export BACKUP_ACCESS_KEY="your-access-key"
export BACKUP_SECRET_KEY="your-secret-key"
export BACKUP_REGION="us-east-1"
```

### 2. Start Backup Service

**Docker Compose:**
```bash
docker compose up -d
```

**Kubernetes:**
```bash
kubectl apply -f k8s/backup.yaml
```

### 3. Create First Backup

```bash
# Via API
curl -X POST http://localhost:8000/backup/create

# Via CLI
python -m src.backup.cli backup
```

## 📋 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BACKUP_PROVIDER` | Storage provider (s3, gcs, azure, local) | `local` | No |
| `BACKUP_DESTINATION` | Backup destination path/bucket | `/backups` | No |
| `BACKUP_SCHEDULE` | Cron schedule for automated backups | `0 2 * * *` | No |
| `BACKUP_RETENTION_DAYS` | Days to keep backups | `30` | No |
| `BACKUP_COMPRESSION` | Enable compression | `true` | No |
| `BACKUP_ENCRYPTION` | Enable encryption | `true` | No |
| `BACKUP_ACCESS_KEY` | Cloud provider access key | - | For cloud |
| `BACKUP_SECRET_KEY` | Cloud provider secret key | - | For cloud |
| `BACKUP_TOKEN` | Service account token (GCS) | - | For GCS |
| `BACKUP_REGION` | Cloud provider region | - | For cloud |

### Provider-Specific Configuration

#### AWS S3
```bash
export BACKUP_PROVIDER="s3"
export BACKUP_DESTINATION="my-backup-bucket/database"
export BACKUP_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
export BACKUP_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export BACKUP_REGION="us-east-1"
```

#### Google Cloud Storage
```bash
export BACKUP_PROVIDER="gcs"
export BACKUP_DESTINATION="my-backup-bucket/database"
export BACKUP_TOKEN='{"type": "service_account", "project_id": "my-project", ...}'
```

#### Azure Blob Storage
```bash
export BACKUP_PROVIDER="azure"
export BACKUP_DESTINATION="mybackupcontainer/database"
export BACKUP_ACCESS_KEY="my-storage-account-name"
export BACKUP_SECRET_KEY="my-storage-account-key"
```

#### Local Filesystem
```bash
export BACKUP_PROVIDER="local"
export BACKUP_DESTINATION="/backups"
```

## 🔧 API Endpoints

### Backup Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/backup/status` | GET | Get backup system status |
| `/backup/create` | POST | Create a new backup |
| `/backup/restore` | POST | Restore a backup |
| `/backup/list` | GET | List available backups |
| `/backup/{name}` | DELETE | Delete a backup |
| `/backup/cleanup` | POST | Clean up old backups |
| `/backup/run-now` | POST | Run backup immediately |
| `/backup/next-backup` | GET | Get next scheduled backup |

### Example API Usage

**Create Backup:**
```bash
curl -X POST http://localhost:8000/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "my-backup-2024-01-15"}'
```

**List Backups:**
```bash
curl http://localhost:8000/backup/list
```

**Restore Backup:**
```bash
curl -X POST http://localhost:8000/backup/restore \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "my-backup-2024-01-15", "target_database": "brownie_metadata"}'
```

**Get Status:**
```bash
curl http://localhost:8000/backup/status
```

## 🖥️ Command Line Interface

### Basic Commands

```bash
# Create backup
python -m src.backup.cli backup --name "my-backup"

# List backups
python -m src.backup.cli list

# Restore backup
python -m src.backup.cli restore my-backup --target-db brownie_metadata

# Delete backup
python -m src.backup.cli delete my-backup

# Clean up old backups
python -m src.backup.cli cleanup

# Show status
python -m src.backup.cli status

# Manage scheduler
python -m src.backup.cli schedule --start
python -m src.backup.cli schedule --stop
python -m src.backup.cli schedule --status
```

### Advanced Usage

```bash
# Create backup with custom name
python -m src.backup.cli backup --name "pre-deployment-backup"

# Restore to different database
python -m src.backup.cli restore my-backup --target-db brownie_metadata_test

# Run cleanup with verbose output
python -m src.backup.cli cleanup --verbose
```

## ⏰ Scheduling

### Cron Schedule Format

The backup system uses standard cron format:
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

### Common Schedules

| Schedule | Description |
|----------|-------------|
| `0 2 * * *` | Daily at 2 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 2 * * 0` | Weekly on Sunday at 2 AM |
| `0 2 1 * *` | Monthly on 1st at 2 AM |
| `0 2 * * 1,3,5` | Monday, Wednesday, Friday at 2 AM |

### Kubernetes CronJob

The system includes a Kubernetes CronJob for automated backups:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: brownie-metadata-db:latest
            command: ["python", "-m", "src.backup.cli", "backup"]
```

## 🔒 Security Features

### Encryption
- **At Rest**: Backups are encrypted before upload
- **In Transit**: HTTPS/TLS for cloud uploads
- **Key Management**: Integration with cloud KMS services

### Access Control
- **IAM Roles**: Cloud provider IAM integration
- **Service Accounts**: GCS service account authentication
- **RBAC**: Kubernetes role-based access control

### Audit Logging
- **Backup Events**: All backup operations logged
- **Access Logs**: Cloud provider access logs
- **Audit Trail**: Complete operation history

## 📊 Monitoring & Alerting

### Backup Metrics
- `backup_total` - Total number of backups created
- `backup_duration_seconds` - Time taken for backup operations
- `backup_size_bytes` - Size of backup files
- `backup_errors_total` - Number of backup failures

### Health Checks
- **Backup Status**: `/backup/status` endpoint
- **Last Backup**: Time of last successful backup
- **Storage Health**: Cloud provider connectivity
- **Retention Policy**: Old backup cleanup status

### Alerting Rules
```yaml
# Example Prometheus alert
- alert: BackupFailed
  expr: increase(backup_errors_total[1h]) > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Backup operation failed"
    description: "Database backup has failed in the last hour"
```

## 🚨 Disaster Recovery

### Recovery Procedures

1. **Identify Latest Backup**
   ```bash
   python -m src.backup.cli list
   ```

2. **Restore Database**
   ```bash
   python -m src.backup.cli restore latest-backup
   ```

3. **Verify Restoration**
   ```bash
   # Check database connectivity
   curl http://localhost:8000/health
   
   # Verify data integrity
   curl http://localhost:8000/backup/status
   ```

### Recovery Time Objectives (RTO)
- **Local Restore**: < 5 minutes
- **Cloud Restore**: < 15 minutes
- **Cross-Region**: < 30 minutes

### Recovery Point Objectives (RPO)
- **Continuous**: WAL archiving (future)
- **Hourly**: Every hour backups
- **Daily**: Daily backups (default)

## 🔧 Troubleshooting

### Common Issues

**Backup Fails with Authentication Error**
```bash
# Check credentials
echo $BACKUP_ACCESS_KEY
echo $BACKUP_SECRET_KEY

# Verify permissions
aws s3 ls s3://your-bucket-name
```

**Backup Fails with Permission Denied**
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name your-user

# Verify bucket access
aws s3api head-bucket --bucket your-bucket-name
```

**Backup Fails with Network Error**
```bash
# Check network connectivity
ping s3.amazonaws.com
telnet s3.amazonaws.com 443

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

**Restore Fails with Database Error**
```bash
# Check database connectivity
psql -h postgres -U brownie -d brownie_metadata -c "SELECT 1"

# Check database permissions
psql -h postgres -U brownie -d brownie_metadata -c "\\l"
```

### Debug Mode

Enable debug logging:
```bash
export BACKUP_DEBUG=true
python -m src.backup.cli backup --verbose
```

### Log Files

- **Application Logs**: `/app/logs/backup.log`
- **Database Logs**: PostgreSQL logs
- **Cloud Logs**: Provider-specific logs

## 📈 Performance Optimization

### Backup Performance
- **Parallel Jobs**: Configure `BACKUP_PARALLEL_JOBS`
- **Compression**: Enable with `BACKUP_COMPRESSION=true`
- **Network**: Use high-bandwidth connections
- **Storage**: Use SSD storage for temporary files

### Restore Performance
- **Pre-warm**: Pre-warm database connections
- **Indexes**: Rebuild indexes after restore
- **Statistics**: Update table statistics
- **Vacuum**: Run VACUUM ANALYZE

### Monitoring Performance
```bash
# Monitor backup duration
curl http://localhost:8000/metrics | grep backup_duration

# Check backup sizes
python -m src.backup.cli list | grep -E "(Size|Created)"

# Monitor storage usage
aws s3 ls s3://your-bucket-name --recursive --human-readable
```

## 🔄 Maintenance

### Regular Tasks
- **Weekly**: Verify backup integrity
- **Monthly**: Test restore procedures
- **Quarterly**: Review retention policies
- **Annually**: Update backup strategies

### Cleanup Procedures
```bash
# Manual cleanup
python -m src.backup.cli cleanup

# Check retention policy
curl http://localhost:8000/backup/status | jq '.retention_days'

# Verify cleanup
python -m src.backup.cli list | wc -l
```

## 📚 Best Practices

### Backup Strategy
1. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
2. **Regular Testing**: Test restore procedures monthly
3. **Monitoring**: Set up alerts for backup failures
4. **Documentation**: Document recovery procedures
5. **Automation**: Use automated scheduling

### Security Best Practices
1. **Encryption**: Always encrypt backups
2. **Access Control**: Use least privilege principle
3. **Audit Logging**: Enable comprehensive logging
4. **Key Management**: Use cloud KMS services
5. **Network Security**: Use VPC endpoints

### Operational Best Practices
1. **Monitoring**: Set up comprehensive monitoring
2. **Alerting**: Configure appropriate alert thresholds
3. **Documentation**: Keep runbooks updated
4. **Training**: Train team on recovery procedures
5. **Testing**: Regular disaster recovery drills

## 🆘 Support

### Getting Help
- **Documentation**: Check this guide first
- **Logs**: Review application and system logs
- **Metrics**: Check Prometheus metrics
- **Community**: GitHub issues and discussions

### Emergency Contacts
- **On-Call**: Your on-call engineer
- **DBA**: Database administrator
- **Cloud Support**: Cloud provider support
- **Vendor Support**: Brownie Metadata support

---

For more information, see the main [README.md](README.md) or contact support.
