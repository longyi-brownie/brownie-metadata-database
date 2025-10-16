# Brownie Metadata Database Helm Chart

Enterprise-grade Helm chart for deploying Brownie Metadata Database on Kubernetes with PostgreSQL read replicas, connection pooling, and automatic failover.

## 🚀 **Quick Start**

### **Install with Helm**
```bash
# Add Helm repository (if using external charts)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install the chart
helm install brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --create-namespace \
  --values ./k8s/helm/values.yaml

# Or with custom values
helm install brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --create-namespace \
  --set app.replicas=5 \
  --set database.patroni.replicas=5 \
  --set monitoring.enabled=true
```

### **Upgrade**
```bash
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --values ./k8s/helm/values.yaml
```

### **Uninstall**
```bash
helm uninstall brownie-metadata-db --namespace brownie-metadata
```

## 📊 **Architecture**

### **Components**
- **Application** - 3 replicas with HPA
- **Patroni** - PostgreSQL HA cluster (3 nodes)
- **PgBouncer** - Connection pooling (2 replicas)
- **Redis** - Caching and sessions
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards

### **High Availability**
- **Automatic failover** with Patroni
- **Read replicas** for scaling reads
- **Connection pooling** with PgBouncer
- **Auto-scaling** with HPA
- **Rolling updates** with zero downtime

## ⚙️ **Configuration**

### **Values File**
```yaml
# k8s/helm/values.yaml
app:
  replicas: 3
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

database:
  patroni:
    enabled: true
    replicas: 3
    storage:
      size: 10Gi
      storageClass: "fast-ssd"

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

### **Environment Variables**
```yaml
config:
  dbHost: "patroni"
  dbPort: 5432
  logLevel: "INFO"
  metricsEnabled: true
```

## 🔧 **Customization**

### **Database Configuration**
```yaml
database:
  type: "patroni"  # Options: patroni, postgresql, external
  
  patroni:
    enabled: true
    replicas: 3
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
    storage:
      size: 10Gi
      storageClass: "fast-ssd"
```

### **Scaling**
```yaml
app:
  replicas: 5
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

### **Monitoring**
```yaml
monitoring:
  enabled: true
  
  prometheus:
    enabled: true
    server:
      persistentVolume:
        enabled: true
        size: 10Gi
        storageClass: "fast-ssd"
  
  grafana:
    enabled: true
    adminPassword: "admin"
    persistence:
      enabled: true
      size: 5Gi
      storageClass: "fast-ssd"
```

## 📈 **Production Deployment**

### **Production Values**
```yaml
# production-values.yaml
global:
  storageClass: "fast-ssd"

app:
  replicas: 5
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 5
    maxReplicas: 20

database:
  patroni:
    replicas: 5
    resources:
      requests:
        memory: "2Gi"
        cpu: "1000m"
      limits:
        memory: "4Gi"
        cpu: "2000m"
    storage:
      size: 50Gi
      storageClass: "fast-ssd"

monitoring:
  enabled: true
  prometheus:
    server:
      persistentVolume:
        size: 50Gi
  grafana:
    persistence:
      size: 20Gi

# Security
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true

# Network policies
networkPolicy:
  enabled: true
```

### **Deploy Production**
```bash
helm install brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --create-namespace \
  --values ./k8s/helm/values.yaml \
  --values production-values.yaml
```

## 🔍 **Monitoring**

### **Access Services**
```bash
# Port forward
kubectl port-forward svc/brownie-metadata-db 8000:8000 -n brownie-metadata
kubectl port-forward svc/brownie-metadata-db-prometheus 9090:9090 -n brownie-metadata
kubectl port-forward svc/brownie-metadata-db-grafana 3000:3000 -n brownie-metadata

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
- Resource utilization

## 🛠️ **Operations**

### **Scaling**
```bash
# Scale application
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --set app.replicas=10

# Scale database
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --set database.patroni.replicas=5
```

### **Updates**
```bash
# Update image
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --set app.image.tag=v1.1.0

# Update configuration
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --set config.logLevel=DEBUG
```

### **Backup**
```bash
# Create backup
kubectl exec -it patroni-0 -n brownie-metadata -- pg_dump -U postgres brownie_metadata > backup.sql

# Restore backup
kubectl exec -i patroni-0 -n brownie-metadata -- psql -U postgres brownie_metadata < backup.sql
```

## 🔒 **Security**

### **Secrets Management**
```yaml
secrets:
  postgresPassword: "YnJvd25pZQ=="  # Base64 encoded
  postgresReplicationPassword: "cmVwbGljYXRvcl9wYXNzd29yZA=="
  jwtSecretKey: "eW91ci1zZWNyZXQta2V5LWhlcmU="
  oktaClientSecret: "eW91ci1va3RhLWNsaWVudC1zZWNyZXQ="
```

### **Network Policies**
```yaml
networkPolicy:
  enabled: true
  ingress:
    enabled: true
  egress:
    enabled: true
```

## 📋 **Troubleshooting**

### **Common Issues**
1. **Pod not starting** - Check resource limits and storage
2. **Database connection failed** - Check Patroni status
3. **High memory usage** - Check connection pool settings
4. **Slow queries** - Check database metrics

### **Debug Commands**
```bash
# Check pod status
kubectl get pods -n brownie-metadata

# Check logs
kubectl logs -f deployment/brownie-metadata-db -n brownie-metadata

# Check Patroni status
kubectl exec -it patroni-0 -n brownie-metadata -- patronictl list

# Check resource usage
kubectl top pods -n brownie-metadata
```

## 📚 **Advanced Usage**

### **Custom Values**
```yaml
# custom-values.yaml
app:
  image:
    repository: my-registry/brownie-metadata-db
    tag: v1.0.0
    pullPolicy: Always

database:
  external:
    enabled: true
    host: "external-postgres.example.com"
    port: 5432
    database: "brownie_metadata"
    username: "brownie"
    password: "brownie"

monitoring:
  prometheus:
    enabled: false
  grafana:
    enabled: false
```

### **Multi-Environment**
```bash
# Development
helm install brownie-metadata-db-dev ./k8s/helm \
  --namespace brownie-metadata-dev \
  --create-namespace \
  --values ./k8s/helm/values.yaml \
  --values dev-values.yaml

# Staging
helm install brownie-metadata-db-staging ./k8s/helm \
  --namespace brownie-metadata-staging \
  --create-namespace \
  --values ./k8s/helm/values.yaml \
  --values staging-values.yaml

# Production
helm install brownie-metadata-db-prod ./k8s/helm \
  --namespace brownie-metadata-prod \
  --create-namespace \
  --values ./k8s/helm/values.yaml \
  --values prod-values.yaml
```

## 🎯 **Best Practices**

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** for all containers
3. **Enable monitoring** in production
4. **Use persistent volumes** for data
5. **Configure backup strategy**
6. **Set up log aggregation**
7. **Use network policies** for security
8. **Monitor resource usage**
9. **Test failover scenarios**
10. **Document configuration changes**
