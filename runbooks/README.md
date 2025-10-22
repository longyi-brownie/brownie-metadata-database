# Brownie Metadata Database - Operational Runbooks

This directory contains comprehensive operational runbooks for managing the Brownie Metadata Database in production environments.

## Available Runbooks

### Core Operations
- **[Database Migration](RUNBOOK-database-migration.md)** - Safe database schema changes and migrations
- **[Database Sharding](RUNBOOK-database-sharding.md)** - Horizontal scaling and sharding strategies
- **[Disaster Recovery](RUNBOOK-disaster-recovery.md)** - Backup, restore, and failover procedures
- **[Scaling Operations](RUNBOOK-scaling-operations.md)** - Vertical and horizontal scaling

### API Integration
- **[Database-API Changes](RUNBOOK-db-api-changes.md)** - Coordinating changes between database and API repositories

### Incident Response
- **[Incident Response](incident-response.md)** - Emergency procedures and troubleshooting (see below)

## Quick Reference

### Emergency Procedures
1. **Database Down**: Check [Disaster Recovery](RUNBOOK-disaster-recovery.md#complete-database-loss)
2. **Migration Failed**: See [Database Migration](RUNBOOK-database-migration.md#rollback-procedures)
3. **Performance Issues**: Review [Scaling Operations](RUNBOOK-scaling-operations.md#performance-monitoring)

### Change Management
1. **Schema Changes**: Follow [Database Migration](RUNBOOK-database-migration.md) process
2. **API Compatibility**: Use [Database-API Changes](RUNBOOK-db-api-changes.md) workflow
3. **Production Deployment**: See [Disaster Recovery](RUNBOOK-disaster-recovery.md#full-system-recovery)

## Contributing

When adding new runbooks:
1. Use clear, step-by-step instructions
2. Include rollback procedures
3. Test procedures in staging first
4. Update this README with new runbook links

---

# Incident Response Procedures

This section contains emergency procedures and troubleshooting for common issues with the Brownie Metadata Database.

## 🚨 Critical Alerts

### Service Down
**Alert**: `ServiceDown`  
**Severity**: Critical  
**Description**: The Brownie Metadata Database service has been down for more than 1 minute.

#### Immediate Actions
1. **Check Service Status**
   ```bash
   # Kubernetes
   kubectl get pods -n brownie-metadata -l app=brownie-metadata-app
   kubectl describe pod -n brownie-metadata <pod-name>
   kubectl logs -n brownie-metadata -l app=brownie-metadata-app --tail=100
   
   # Docker Compose
   docker compose ps
   docker compose logs app
   ```

2. **Check Resource Usage**
   ```bash
   # Kubernetes
   kubectl top pods -n brownie-metadata
   
   # Docker Compose
   docker stats
   ```

3. **Restart Service**
   ```bash
   # Kubernetes
   kubectl rollout restart deployment/brownie-metadata-app -n brownie-metadata
   
   # Docker Compose
   docker compose restart app
   ```

4. **Check Dependencies**
   - Database connectivity
   - Redis connectivity
   - Network issues

#### Escalation
- If service doesn't start within 5 minutes, escalate to on-call engineer
- If database issues, contact DBA team
- If infrastructure issues, contact platform team

---

### Critical Error Rate
**Alert**: `CriticalErrorRate`  
**Severity**: Critical  
**Description**: Error rate is above 10% for the last 5 minutes.

#### Immediate Actions
1. **Check Error Logs**
   ```bash
   kubectl logs -n brownie-metadata -l app=brownie-metadata-app --tail=200 | grep ERROR
   ```

2. **Identify Error Patterns**
   - Database connection errors
   - Authentication failures
   - Validation errors
   - External service failures

3. **Check System Resources**
   ```bash
   kubectl top pods -n brownie-metadata
   kubectl describe nodes
   ```

4. **Scale Up if Needed**
   ```bash
   kubectl scale deployment brownie-metadata-app --replicas=3 -n brownie-metadata
   ```

#### Common Causes
- Database connection pool exhaustion
- Memory leaks
- High load causing timeouts
- External service degradation

---

### Critical Response Time
**Alert**: `CriticalResponseTime`  
**Severity**: Critical  
**Description**: 95th percentile response time is above 5 seconds.

#### Immediate Actions
1. **Check Database Performance**
   ```sql
   -- Check active queries
   SELECT pid, state, query_start, query 
   FROM pg_stat_activity 
   WHERE state = 'active' 
   ORDER BY query_start;
   
   -- Check slow queries
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. **Check Application Metrics**
   ```bash
   curl http://localhost:8000/metrics | grep request_duration
   ```

3. **Scale Resources**
   ```bash
   # Scale up replicas
   kubectl scale deployment brownie-metadata-app --replicas=5 -n brownie-metadata
   
   # Increase resource limits
   kubectl patch deployment brownie-metadata-app -n brownie-metadata -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"cpu":"1000m","memory":"2Gi"}}}]}}}}'
   ```

---

## ⚠️ Warning Alerts

### High Error Rate
**Alert**: `HighErrorRate`  
**Severity**: Warning  
**Description**: Error rate is above 5% for the last 5 minutes.

#### Actions
1. **Monitor Error Trends**
   ```bash
   # Check error rate over time
   curl -s http://localhost:8000/metrics | grep errors_total
   ```

2. **Check Recent Deployments**
   - Review recent changes
   - Check configuration changes
   - Verify dependency updates

3. **Analyze Error Types**
   - Categorize errors by type
   - Identify root causes
   - Plan fixes

---

### High Response Time
**Alert**: `HighResponseTime`  
**Severity**: Warning  
**Description**: 95th percentile response time is above 2 seconds.

#### Actions
1. **Performance Analysis**
   ```bash
   # Check response time percentiles
   curl -s http://localhost:8000/metrics | grep request_duration_seconds
   ```

2. **Database Optimization**
   - Check for missing indexes
   - Analyze query performance
   - Consider query optimization

3. **Resource Monitoring**
   - Monitor CPU usage
   - Check memory consumption
   - Review network latency

---

### Database Connection High
**Alert**: `DatabaseConnectionHigh`  
**Severity**: Warning  
**Description**: Database has more than 80 active connections.

#### Actions
1. **Check Connection Pool**
   ```bash
   # Check active connections
   curl -s http://localhost:8000/metrics | grep db_connections_active
   ```

2. **Database Analysis**
   ```sql
   -- Check connection count
   SELECT count(*) FROM pg_stat_activity;
   
   -- Check idle connections
   SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';
   ```

3. **Optimize Connections**
   - Review connection pool settings
   - Check for connection leaks
   - Consider connection pooling

---

## 📊 Business Metrics Alerts

### High Incident Volume
**Alert**: `HighIncidentVolume`  
**Severity**: Warning  
**Description**: More than 10 incidents created in the last hour.

#### Actions
1. **Analyze Incident Patterns**
   - Check incident types
   - Identify common causes
   - Review user reports

2. **Check System Health**
   - Verify all services are running
   - Check for recent issues
   - Review error logs

3. **Communication**
   - Update status page
   - Notify stakeholders
   - Prepare incident report

---

### Long Incident Resolution
**Alert**: `LongIncidentResolution`  
**Severity**: Warning  
**Description**: 95th percentile incident resolution time is above 60 minutes.

#### Actions
1. **Review Active Incidents**
   - Check incident age
   - Identify blockers
   - Assign additional resources

2. **Process Improvement**
   - Review resolution procedures
   - Update documentation
   - Train team members

---

## 🔧 Troubleshooting Commands

### General Health Checks
```bash
# Service status
kubectl get pods -n brownie-metadata
kubectl get svc -n brownie-metadata

# Logs
kubectl logs -n brownie-metadata -l app=brownie-metadata-app --tail=100

# Metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

### Database Commands
```bash
# Connect to database
kubectl exec -it -n brownie-metadata <postgres-pod> -- psql -U brownie -d brownie_metadata

# Check database size
kubectl exec -it -n brownie-metadata <postgres-pod> -- psql -U brownie -d brownie_metadata -c "SELECT pg_size_pretty(pg_database_size('brownie_metadata'));"

# Check table sizes
kubectl exec -it -n brownie-metadata <postgres-pod> -- psql -U brownie -d brownie_metadata -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Performance Analysis
```bash
# Check resource usage
kubectl top pods -n brownie-metadata
kubectl top nodes

# Check network connectivity
kubectl exec -it -n brownie-metadata <app-pod> -- curl -I http://postgres:5432
kubectl exec -it -n brownie-metadata <app-pod> -- curl -I http://redis:6379

# Check disk usage
kubectl exec -it -n brownie-metadata <postgres-pod> -- df -h
```

## 📞 Escalation Procedures

### Level 1 (0-15 minutes)
- On-call engineer
- Basic troubleshooting
- Service restart

### Level 2 (15-30 minutes)
- Senior engineer
- Advanced troubleshooting
- Configuration changes

### Level 3 (30+ minutes)
- Engineering manager
- Architecture review
- External vendor support

## 📋 Post-Incident Actions

1. **Incident Review**
   - Document timeline
   - Identify root cause
   - Note lessons learned

2. **Action Items**
   - Fix identified issues
   - Update monitoring
   - Improve documentation

3. **Follow-up**
   - Schedule post-mortem
   - Update runbooks
   - Share learnings

## 🔗 Useful Links

- [Grafana Dashboard](http://localhost:3000)
- [Prometheus Metrics](http://localhost:9090)
- [AlertManager](http://localhost:9093)
- [Database Admin](http://localhost:8080/admin)
- [API Documentation](http://localhost:8000/docs)
