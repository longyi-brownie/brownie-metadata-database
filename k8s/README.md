# Kubernetes Deployment for Brownie Metadata Database

Enterprise-grade Kubernetes deployment with PostgreSQL read replicas, connection pooling, and automatic failover.

## 🏗️ **Architecture**

### **Database Layer**
- **Patroni** - PostgreSQL HA with automatic failover
- **3 PostgreSQL instances** - 1 primary + 2 replicas
- **PgBouncer** - Connection pooling (2 replicas)
- **Redis** - Caching and session storage

### **Application Layer**
- **3 App replicas** - Load balanced
- **HPA** - Auto-scaling based on CPU/memory
- **Ingress** - External access with SSL

### **Monitoring Layer**
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization

## 🚀 **Quick Start**

### **Prerequisites**
- Kubernetes cluster (1.20+)
- kubectl configured
- Storage class available (adjust `storageClassName` in manifests)

### **Deploy Everything**
```bash
# Apply all resources
kubectl apply -k k8s/

# Or apply individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/patroni.yaml
kubectl apply -f k8s/pgbouncer.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/monitoring.yaml
```

### **Check Status**
```bash
# Check all pods
kubectl get pods -n brownie-metadata

# Check services
kubectl get svc -n brownie-metadata

# Check Patroni status
kubectl exec -it patroni-0 -n brownie-metadata -- patronictl list

# Check logs
kubectl logs -f deployment/brownie-metadata-app -n brownie-metadata
```

## 🔧 **Configuration**

### **Database Configuration**
```yaml
# k8s/configmap.yaml
data:
  DB_HOST: "patroni"  # Patroni service
  DB_PORT: "5432"
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "30"
```

### **Scaling**
```bash
# Scale app replicas
kubectl scale deployment brownie-metadata-app --replicas=5 -n brownie-metadata

# Scale PgBouncer
kubectl scale deployment pgbouncer --replicas=3 -n brownie-metadata

# Check HPA status
kubectl get hpa -n brownie-metadata
```

### **Storage**
Adjust storage classes in manifests:
```yaml
storageClassName: "fast-ssd"  # Change to your storage class
```

## 📊 **Monitoring**

### **Access Services**
```bash
# Port forward for local access
kubectl port-forward svc/brownie-metadata-app 8000:8000 -n brownie-metadata
kubectl port-forward svc/prometheus 9090:9090 -n brownie-metadata
kubectl port-forward svc/grafana 3000:3000 -n brownie-metadata

# Access URLs
# App: http://localhost:8000
# Metrics: http://localhost:8001/metrics
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### **Key Metrics**
- Database query performance
- Connection pool utilization
- Application response times
- Error rates and availability

## 🔄 **High Availability Features**

### **Patroni Automatic Failover**
- **Leader election** - Automatic primary selection
- **Health checks** - Continuous monitoring
- **Failover time** - ~30 seconds
- **Data consistency** - Synchronous replication

### **Connection Pooling**
- **PgBouncer** - Transaction-level pooling
- **Load balancing** - Read/write separation
- **Connection limits** - Prevents database overload

### **Application Resilience**
- **Multiple replicas** - No single point of failure
- **Health checks** - Automatic restart on failure
- **Rolling updates** - Zero-downtime deployments

## 🛠️ **Operations**

### **Database Operations**
```bash
# Check Patroni cluster status
kubectl exec -it patroni-0 -n brownie-metadata -- patronictl list

# Promote replica to primary (if needed)
kubectl exec -it patroni-0 -n brownie-metadata -- patronictl failover

# Check PostgreSQL logs
kubectl logs patroni-0 -n brownie-metadata
```

### **Backup and Recovery**
```bash
# Create backup
kubectl exec -it patroni-0 -n brownie-metadata -- pg_dump -U postgres brownie_metadata > backup.sql

# Restore backup
kubectl exec -i patroni-0 -n brownie-metadata -- psql -U postgres brownie_metadata < backup.sql
```

### **Scaling Operations**
```bash
# Scale up database
kubectl scale statefulset patroni --replicas=5 -n brownie-metadata

# Scale down (be careful!)
kubectl scale statefulset patroni --replicas=3 -n brownie-metadata
```

## 🔒 **Security**

### **Secrets Management**
- Use Kubernetes secrets for sensitive data
- Consider external secret management (Vault, etc.)
- Rotate secrets regularly

### **Network Policies**
```yaml
# Example network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: brownie-metadata-netpol
  namespace: brownie-metadata
spec:
  podSelector:
    matchLabels:
      app: brownie-metadata-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: brownie-metadata
    ports:
    - protocol: TCP
      port: 8000
```

## 📈 **Performance Tuning**

### **Database Tuning**
- Adjust PostgreSQL parameters in Patroni config
- Monitor connection pool utilization
- Tune memory and CPU limits

### **Application Tuning**
- Adjust HPA thresholds
- Monitor response times
- Optimize database queries

### **Monitoring Tuning**
- Adjust scrape intervals
- Configure alerting rules
- Set up log aggregation

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Pod not starting** - Check resource limits and storage
2. **Database connection failed** - Check Patroni status
3. **High memory usage** - Check connection pool settings
4. **Slow queries** - Check database metrics

### **Debug Commands**
```bash
# Check pod status
kubectl describe pod <pod-name> -n brownie-metadata

# Check logs
kubectl logs <pod-name> -n brownie-metadata

# Check events
kubectl get events -n brownie-metadata

# Check resource usage
kubectl top pods -n brownie-metadata
```

## 🔄 **Upgrades**

### **Application Updates**
```bash
# Update image
kubectl set image deployment/brownie-metadata-app app=brownie-metadata-db:v1.1.0 -n brownie-metadata

# Check rollout status
kubectl rollout status deployment/brownie-metadata-app -n brownie-metadata

# Rollback if needed
kubectl rollout undo deployment/brownie-metadata-app -n brownie-metadata
```

### **Database Updates**
- Patroni handles rolling updates automatically
- Test in staging environment first
- Have backup and rollback plan ready

## 📋 **Production Checklist**

- [ ] Configure proper storage classes
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Set up log aggregation
- [ ] Configure network policies
- [ ] Set up SSL/TLS certificates
- [ ] Configure resource quotas
- [ ] Set up disaster recovery
- [ ] Configure security scanning
- [ ] Set up compliance monitoring
