# Runbook: Scaling Operations

This runbook covers horizontal and vertical scaling procedures for the Brownie Metadata Database.

## TL;DR
- Horizontal scaling: Add read replicas and app replicas
- Vertical scaling: Increase CPU/memory resources
- Sharding: Partition data by organization
- Monitor performance before and after scaling

---

## 1) Horizontal Scaling

### Add Read Replicas
```bash
# 1. Deploy additional read replica
kubectl apply -f k8s/postgres-replicas.yaml

# 2. Scale read replicas
kubectl scale statefulset postgres-replica --replicas=3 -n brownie-metadata

# 3. Verify replicas are ready
kubectl wait --for=condition=ready pod -l app=postgres-replica -n brownie-metadata --timeout=300s

# 4. Check replication status
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT client_addr, state, sync_state, sync_priority 
FROM pg_stat_replication;
"
```

### Scale Application Replicas
```bash
# 1. Check current resource usage
kubectl top pods -n brownie-metadata

# 2. Scale application horizontally
kubectl scale deployment brownie-metadata-app --replicas=5 -n brownie-metadata

# 3. Verify HPA is working
kubectl get hpa -n brownie-metadata

# 4. Monitor scaling events
kubectl get events -n brownie-metadata --sort-by='.lastTimestamp'
```

### Load Balancer Configuration
```yaml
# Update service to use multiple replicas
apiVersion: v1
kind: Service
metadata:
  name: brownie-metadata-app
spec:
  selector:
    app: brownie-metadata-app
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
  sessionAffinity: None  # Enable for sticky sessions if needed
```

---

## 2) Vertical Scaling

### Increase Database Resources
```bash
# 1. Update resource limits
kubectl patch statefulset postgres-primary -n brownie-metadata -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "postgres",
          "resources": {
            "requests": {"cpu": "2", "memory": "4Gi"},
            "limits": {"cpu": "4", "memory": "8Gi"}
          }
        }]
      }
    }
  }
}'

# 2. Monitor resource usage
kubectl top pods -n brownie-metadata

# 3. Check database performance
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched
FROM pg_stat_database 
WHERE datname = 'brownie_metadata';
"
```

### Increase Application Resources
```bash
# 1. Update deployment resources
kubectl patch deployment brownie-metadata-app -n brownie-metadata -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "requests": {"cpu": "500m", "memory": "1Gi"},
            "limits": {"cpu": "1", "memory": "2Gi"}
          }
        }]
      }
    }
  }
}'

# 2. Update HPA thresholds
kubectl patch hpa brownie-metadata-app -n brownie-metadata -p '
{
  "spec": {
    "minReplicas": 2,
    "maxReplicas": 10,
    "metrics": [{
      "type": "Resource",
      "resource": {
        "name": "cpu",
        "target": {
          "type": "Utilization",
          "averageUtilization": 70
        }
      }
    }]
  }
}'
```

---

## 3) Database Sharding

### Organization-Based Sharding
```bash
# 1. Create shard databases
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
CREATE DATABASE brownie_metadata_shard_1;
CREATE DATABASE brownie_metadata_shard_2;
CREATE DATABASE brownie_metadata_shard_3;
"

# 2. Deploy shard-specific applications
kubectl apply -f k8s/shard-1.yaml -n brownie-metadata
kubectl apply -f k8s/shard-2.yaml -n brownie-metadata
kubectl apply -f k8s/shard-3.yaml -n brownie-metadata

# 3. Configure shard routing
kubectl create configmap shard-routing -n brownie-metadata --from-literal=shard-1="orgs_1-1000"
kubectl create configmap shard-routing -n brownie-metadata --from-literal=shard-2="orgs_1001-2000"
kubectl create configmap shard-routing -n brownie-metadata --from-literal=shard-3="orgs_2001+"
```

### Shard Migration
```bash
# 1. Identify organizations to migrate
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT id, name FROM organizations 
WHERE id BETWEEN 1001 AND 2000 
ORDER BY id;
"

# 2. Export organization data
kubectl exec -n brownie-metadata deployment/postgres-primary -- pg_dump \
  -d brownie_metadata \
  -t organizations \
  -t incidents \
  -t users \
  -t teams \
  -t agent_configs \
  --where="organization_id BETWEEN 1001 AND 2000" \
  > shard_2_data.sql

# 3. Import to shard database
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -d brownie_metadata_shard_2 -f shard_2_data.sql

# 4. Verify data integrity
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT COUNT(*) FROM brownie_metadata_shard_2.organizations;
SELECT COUNT(*) FROM brownie_metadata_shard_2.incidents;
"
```

---

## 4) Performance Monitoring

### Before Scaling
```bash
# Baseline performance metrics
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
import time
import requests

# Measure response times
start = time.time()
response = requests.get('http://localhost:8000/health')
end = time.time()
print(f'Health check response time: {end - start:.3f}s')

# Measure database query performance
start = time.time()
response = requests.get('http://localhost:8000/metrics')
end = time.time()
print(f'Metrics endpoint response time: {end - start:.3f}s')
"
```

### After Scaling
```bash
# Compare performance metrics
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
import time
import requests

# Measure response times
start = time.time()
response = requests.get('http://localhost:8000/health')
end = time.time()
print(f'Health check response time: {end - start:.3f}s')

# Check database connection pool
response = requests.get('http://localhost:8000/metrics')
print('Database connection pool metrics:')
for line in response.text.split('\n'):
    if 'db_connections' in line:
        print(line)
"
```

### Database Performance
```bash
# Check query performance
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"

# Check index usage
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;
"
```

---

## 5) Auto-Scaling Configuration

### HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: brownie-metadata-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: brownie-metadata-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### VPA Configuration
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: brownie-metadata-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: brownie-metadata-app
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
```

---

## 6) Capacity Planning

### Resource Requirements
```bash
# Calculate current resource usage
kubectl top pods -n brownie-metadata

# Estimate future requirements
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
import psutil
import time

# Monitor resource usage over time
for i in range(60):  # 1 minute
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f'CPU: {cpu_percent}%, Memory: {memory.percent}%')
    time.sleep(1)
"
```

### Growth Projections
```bash
# Analyze data growth
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Check table growth rates
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;
"
```

---

## 7) Scaling Validation

### Load Testing
```bash
# Run load test
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
import asyncio
import aiohttp
import time

async def make_request(session, url):
    async with session.get(url) as response:
        return await response.text()

async def load_test():
    url = 'http://localhost:8000/health'
    concurrent_requests = 100
    duration = 60  # seconds
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            for _ in range(concurrent_requests):
                task = asyncio.create_task(make_request(session, url))
                tasks.append(task)
            
            # Wait a bit before next batch
            await asyncio.sleep(0.1)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f'Successful requests: {successful}')
        print(f'Failed requests: {failed}')
        print(f'Success rate: {successful/len(results)*100:.2f}%')

asyncio.run(load_test())
"
```

### Performance Benchmarks
```bash
# Database performance benchmarks
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
-- Test query performance
EXPLAIN ANALYZE SELECT * FROM incidents WHERE organization_id = 1;

-- Test index usage
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Test join performance
EXPLAIN ANALYZE 
SELECT i.*, o.name as org_name 
FROM incidents i 
JOIN organizations o ON i.organization_id = o.id 
WHERE i.created_at > NOW() - INTERVAL '7 days';
"
```

---

## 8) Rollback Procedures

### Scale Down
```bash
# Scale down application
kubectl scale deployment brownie-metadata-app --replicas=1 -n brownie-metadata

# Scale down database replicas
kubectl scale statefulset postgres-replica --replicas=1 -n brownie-metadata

# Monitor for issues
kubectl get pods -n brownie-metadata
kubectl logs -f -n brownie-metadata deployment/brownie-metadata-app
```

### Resource Rollback
```bash
# Revert resource changes
kubectl patch deployment brownie-metadata-app -n brownie-metadata -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "requests": {"cpu": "250m", "memory": "512Mi"},
            "limits": {"cpu": "500m", "memory": "1Gi"}
          }
        }]
      }
    }
  }
}'
```

---

## 9) Definition of Done

- [ ] Scaling objectives met
- [ ] Performance metrics improved
- [ ] Resource utilization optimized
- [ ] Monitoring and alerting updated
- [ ] Load testing completed
- [ ] Rollback procedures tested
- [ ] Documentation updated
- [ ] Team notified of changes
