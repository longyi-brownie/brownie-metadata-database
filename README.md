# Brownie Metadata Database

Enterprise-ready, containerized database service for Brownie incident assistant. Provides metadata storage for organizations, teams, users, incidents, agent configurations, and analytics.

## Features

- **Multi-tenant Architecture**: Organization-scoped data with team-based RBAC
- **Enterprise Logging**: Structured logging with audit trails and performance monitoring
- **Prometheus Metrics**: Comprehensive metrics collection for monitoring and alerting
- **Database Migrations**: Alembic-based schema management
- **High Availability**: Patroni PostgreSQL cluster with automatic failover
- **Read Replicas**: Horizontal database scaling for read-heavy workloads
- **Connection Pooling**: PgBouncer for 1000+ concurrent connections
- **Auto-scaling**: Kubernetes HPA based on CPU/memory metrics
- **Containerized**: Docker Compose for development, Kubernetes for production
- **Testing**: Comprehensive test suite with fixtures and mocks

## Tech Stack

- **Python 3.12**
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations
- **PostgreSQL 16** - Primary database
- **Redis** - Caching and sessions
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **structlog** - Structured logging
- **pytest** - Testing framework

## Quick Start

### Prerequisites

- **Docker Compose**: Docker and Docker Compose
- **Kubernetes**: Kubernetes cluster (1.20+) and kubectl
- **Local Development**: Python 3.12+

## Database Operations

### When to Run Migrations

Run `python3 -m alembic upgrade head` in these scenarios:

- **After pulling code changes** that include new migrations
- **Before starting the application** for the first time
- **After creating new models** or modifying existing ones
- **When deploying to a new environment**
- **After switching branches** that have different schema versions

### Migration Commands

```bash
# Apply all pending migrations
python3 -m alembic upgrade head

# Apply migrations up to a specific revision
python3 -m alembic upgrade <revision_id>

# Rollback to previous migration
python3 -m alembic downgrade -1

# Rollback to base (empty database)
python3 -m alembic downgrade base

# Check current migration status
python3 -m alembic current

# Show migration history
python3 -m alembic history

# Create a new migration (after model changes)
python3 -m alembic revision --autogenerate -m "Description of changes"
```

### Database Access & Debugging

#### Connect to PostgreSQL Console

**Docker Compose:**
```bash
# Connect to the database
docker exec -it brownie-metadata-postgres psql -U brownie -d brownie_metadata

# Or using docker-compose
docker-compose exec postgres psql -U brownie -d brownie_metadata
```

### Runbooks

- [Coordinating DB Schema Changes with the Metadata API](docs/RUNBOOK-db-api-changes.md)

**Kubernetes:**
```bash
# Get pod name
kubectl get pods -n brownie-metadata

# Connect to database
kubectl exec -it <postgres-pod-name> -n brownie-metadata -- psql -U brownie -d brownie_metadata
```

#### Useful PostgreSQL Commands

```sql
-- List all tables
\dt

-- Describe table structure
\d table_name

-- List all databases
\l

-- List all schemas
\dn

-- List all users/roles
\du

-- Show current database
SELECT current_database();

-- Show current user
SELECT current_user;

-- Exit psql
\q
```

#### Debugging Queries

```sql
-- Check table contents
SELECT * FROM organizations LIMIT 5;
SELECT * FROM teams LIMIT 5;
SELECT * FROM users LIMIT 5;
SELECT * FROM incidents LIMIT 5;
SELECT * FROM configs LIMIT 5;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## Enterprise Monitoring & Observability

### Grafana Dashboard

The Brownie Metadata Database includes a comprehensive, enterprise-ready Grafana dashboard that provides real-time insights into system performance, business metrics, and operational health.

#### Dashboard Features

**📊 Performance Metrics:**
- **Request Rate (RPS)**: Real-time request throughput by endpoint and method
- **Response Time**: P50, P95, P99 latency percentiles for SLA monitoring
- **Error Rate**: Application error tracking and alerting
- **Database Performance**: Query rate, transaction rate, and connection monitoring

**🏢 Business Metrics:**
- **User Analytics**: Total users, active users, and user growth trends
- **Organization Metrics**: Multi-tenant organization and team tracking
- **Incident Management**: Total incidents, active incidents, and resolution time tracking

**🔧 Operational Health:**
- **Database Health**: Active connections, query duration, and error rates
- **System Resources**: CPU, memory, and storage utilization
- **Service Availability**: Uptime monitoring and health checks

#### Dashboard Installation

**Option 1: Kubernetes (Recommended)**
```bash
# Apply the dashboard configuration
kubectl apply -f grafana-dashboard-config.yaml

# Access Grafana (port-forward or ingress)
kubectl port-forward -n brownie-metadata svc/grafana 3000:3000
# Open http://localhost:3000 (admin/admin)
```

**Option 2: Docker Compose**
```bash
# Dashboard is automatically loaded in Grafana
docker compose up -d
# Access http://localhost:3000 (admin/admin)
```

**Option 3: Manual Import**
1. Open Grafana at http://localhost:3000
2. Go to "+" → "Import"
3. Upload `grafana-dashboard.json`
4. Configure Prometheus data source if needed

#### Key Metrics Explained

| Metric | Type | Description | Business Value |
|--------|------|-------------|----------------|
| `requests_total` | Counter | Total HTTP requests | Traffic volume and growth |
| `request_duration_seconds` | Histogram | Request latency | Performance and SLA compliance |
| `users_total` | Gauge | Total registered users | Customer base growth |
| `users_active` | Gauge | Currently active users | Engagement and usage |
| `incidents_total` | Counter | Total incidents created | Support workload |
| `incidents_active` | Gauge | Currently open incidents | Support queue status |
| `incident_resolution_time_minutes` | Histogram | Time to resolve incidents | Support efficiency |
| `db_queries_total` | Counter | Database query count | Database load |
| `db_query_duration_seconds` | Histogram | Query execution time | Database performance |
| `db_connections_active` | Gauge | Active DB connections | Resource utilization |
| `errors_total` | Counter | Application errors | System reliability |

#### Alerting Rules

The dashboard includes recommended alerting thresholds:

- **High Error Rate**: > 5% error rate for 5 minutes
- **High Latency**: P95 response time > 2 seconds
- **Database Issues**: Query duration P95 > 1 second
- **High Incident Volume**: > 10 new incidents per hour
- **Resource Exhaustion**: > 80% CPU or memory usage

#### Customization

The dashboard is fully customizable for enterprise needs:

1. **Add Custom Metrics**: Extend the metrics collection in your application
2. **Modify Thresholds**: Adjust alerting rules for your SLA requirements
3. **Add Business KPIs**: Include revenue, conversion, or other business metrics
4. **Multi-Environment**: Create separate dashboards for dev/staging/prod

#### Enterprise Features

- **Multi-tenant Monitoring**: Organization-scoped metrics and dashboards
- **Role-based Access**: Different views for operators, managers, and executives
- **Automated Reporting**: Scheduled reports and executive summaries
- **Integration Ready**: Webhook support for PagerDuty, Slack, email alerts
- **Compliance**: Audit trails and data retention policies

### Enterprise Alerting & Incident Response

The Brownie Metadata Database includes comprehensive, enterprise-grade alerting with multiple notification channels and automated incident response procedures.

#### Alert Categories

**🚨 Critical Alerts (Immediate Response)**
- Service Down - Service unavailable for >1 minute
- Critical Error Rate - Error rate >10% for 5 minutes
- Critical Response Time - P95 latency >5 seconds
- Database Connection Critical - >95 active connections
- SLA Breach - 99th percentile >10 seconds
- Potential DDoS - >500 requests/second

**⚠️ Warning Alerts (15-minute Response)**
- High Error Rate - Error rate >5% for 5 minutes
- High Response Time - P95 latency >2 seconds
- Database Connection High - >80 active connections
- High Incident Volume - >10 incidents/hour
- Long Incident Resolution - P95 >60 minutes
- High CPU/Memory Usage - >80% utilization

**ℹ️ Info Alerts (Monitoring)**
- User Growth Anomaly - >1000 new users/hour
- Unusual Query Pattern - >100 queries/second
- Data Integrity Issues - Constraint violations

#### Notification Channels

**PagerDuty Integration**
- Critical alerts → Immediate escalation
- On-call rotation support
- Escalation policies
- Mobile app notifications

**Slack Integration**
- Real-time alerts in dedicated channels
- Rich formatting with runbook links
- Team collaboration features
- Custom webhook support

**Email Notifications**
- Detailed incident reports
- Executive summaries
- Runbook links and context
- Escalation chains

**Microsoft Teams**
- Enterprise chat integration
- Rich card notifications
- Team collaboration
- Mobile notifications

#### Alerting Rules Configuration

**Prometheus Alert Rules**
```yaml
# Example: High Error Rate Alert
- alert: HighErrorRate
  expr: rate(errors_total[5m]) / rate(requests_total[5m]) > 0.05
  for: 2m
  labels:
    severity: warning
    service: brownie-metadata-database
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes."
    runbook_url: "https://docs.brownie-metadata.com/runbooks/high-error-rate"
```

**AlertManager Configuration**
- Intelligent grouping and deduplication
- Escalation policies
- Silence and inhibition rules
- Multi-channel routing

#### Incident Response Runbooks

Comprehensive runbooks are provided for all alert types:

1. **Immediate Actions** - First 5 minutes
2. **Diagnostic Steps** - Root cause analysis
3. **Resolution Procedures** - Step-by-step fixes
4. **Escalation Paths** - When to escalate
5. **Post-Incident Actions** - Follow-up procedures

**Key Runbooks Include:**
- Service Down Recovery
- Database Performance Issues
- High Error Rate Resolution
- Security Incident Response
- SLA Breach Recovery

#### Alerting Installation

**Kubernetes (Recommended)**
```bash
# Apply alerting configuration
kubectl apply -f k8s/alerting.yaml

# Check alert status
kubectl get pods -n brownie-metadata -l app=alertmanager
kubectl port-forward -n brownie-metadata svc/alertmanager 9093:9093

# Access AlertManager
open http://localhost:9093
```

**Docker Compose**
```bash
# Alerting is included in the monitoring stack
docker compose up -d
# Access AlertManager at http://localhost:9093
```

#### Alert Testing

**Test Alert Rules**
```bash
# Trigger test alert
kubectl exec -it -n brownie-metadata <app-pod> -- curl -X POST http://localhost:8000/test-alert

# Check alert status
curl http://localhost:9093/api/v1/alerts
```

**Validate Notifications**
- Test PagerDuty integration
- Verify Slack webhook delivery
- Check email delivery
- Validate escalation chains

#### Customization

**Add Custom Alerts**
1. Define new Prometheus rules
2. Configure notification channels
3. Create runbook documentation
4. Test alert scenarios

**Modify Thresholds**
- Adjust alert sensitivity
- Set business-specific SLAs
- Configure escalation timing
- Customize notification content

**Integration Examples**
- Jira ticket creation
- ServiceNow integration
- Custom webhook endpoints
- Third-party monitoring tools

## Enterprise Backup & Disaster Recovery

The Brownie Metadata Database includes a comprehensive, enterprise-ready backup system that works out of the box with minimal configuration.

### 🚀 Quick Start

**1. Configure Backup Settings**
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

**2. Start Backup Service**
```bash
# Docker Compose
docker compose up -d

# Kubernetes
kubectl apply -f k8s/backup.yaml
```

**3. Create First Backup**
```bash
# Via API
curl -X POST http://localhost:8000/backup/create

# Via CLI
python -m src.backup.cli backup
```

### 📋 Supported Providers

| Provider | Configuration | Features |
|----------|---------------|----------|
| **AWS S3** | Access key + Secret key | Encryption, Lifecycle, Cross-region |
| **Google Cloud Storage** | Service account JSON | Encryption, Lifecycle, Multi-region |
| **Azure Blob Storage** | Account name + Key | Encryption, Lifecycle, Geo-redundancy |
| **Local Filesystem** | Directory path | Compression, Encryption |

### 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/backup/status` | GET | Get backup system status |
| `/backup/create` | POST | Create a new backup |
| `/backup/restore` | POST | Restore a backup |
| `/backup/list` | GET | List available backups |
| `/backup/{name}` | DELETE | Delete a backup |
| `/backup/cleanup` | POST | Clean up old backups |
| `/backup/run-now` | POST | Run backup immediately |

### 🖥️ Command Line Interface

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
```

### ⏰ Automated Scheduling

**Cron Schedule Format**
```bash
# Daily at 2 AM
export BACKUP_SCHEDULE="0 2 * * *"

# Every 6 hours
export BACKUP_SCHEDULE="0 */6 * * *"

# Weekly on Sunday at 2 AM
export BACKUP_SCHEDULE="0 2 * * 0"

# Monthly on 1st at 2 AM
export BACKUP_SCHEDULE="0 2 1 * *"
```

**Kubernetes CronJob**
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

### 🔒 Security Features

- **Encryption**: At-rest and in-transit encryption
- **Access Control**: IAM roles and service accounts
- **Audit Logging**: Complete operation history
- **Key Management**: Cloud KMS integration
- **Network Security**: VPC endpoints and private networks

### 📊 Monitoring & Alerting

**Backup Metrics**
- `backup_total` - Total number of backups created
- `backup_duration_seconds` - Time taken for backup operations
- `backup_size_bytes` - Size of backup files
- `backup_errors_total` - Number of backup failures

**Health Checks**
- Backup status endpoint
- Last backup timestamp
- Storage health monitoring
- Retention policy compliance

### 🚨 Disaster Recovery

**Recovery Procedures**
1. Identify latest backup
2. Restore database
3. Verify restoration
4. Update application

**Recovery Time Objectives (RTO)**
- Local restore: < 5 minutes
- Cloud restore: < 15 minutes
- Cross-region: < 30 minutes

**Recovery Point Objectives (RPO)**
- Continuous: WAL archiving (future)
- Hourly: Every hour backups
- Daily: Daily backups (default)

### 📈 Performance Optimization

- **Parallel Jobs**: Configure `BACKUP_PARALLEL_JOBS`
- **Compression**: Enable with `BACKUP_COMPRESSION=true`
- **Network**: Use high-bandwidth connections
- **Storage**: Use SSD storage for temporary files

### 🔄 Maintenance

**Regular Tasks**
- Weekly: Verify backup integrity
- Monthly: Test restore procedures
- Quarterly: Review retention policies
- Annually: Update backup strategies

**Cleanup Procedures**
```bash
# Manual cleanup
python -m src.backup.cli cleanup

# Check retention policy
curl http://localhost:8000/backup/status | jq '.retention_days'
```

### 📚 Best Practices

1. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
2. **Regular Testing**: Test restore procedures monthly
3. **Monitoring**: Set up alerts for backup failures
4. **Documentation**: Document recovery procedures
5. **Automation**: Use automated scheduling

For detailed backup documentation, see [BACKUP.md](BACKUP.md).

### Common Troubleshooting

#### Kubernetes Issues

**Problem**: `kubectl: command not found`
```bash
# Install kubectl
# macOS with Homebrew:
brew install kubectl

# Or download from: https://kubernetes.io/docs/tasks/tools/
```

**Problem**: `The connection to the server localhost:8080 was refused`
```bash
# This means no Kubernetes cluster is running
# Choose one of the cluster setup options above

# For minikube:
minikube start

# For Docker Desktop:
# Enable Kubernetes in Docker Desktop settings

# For kind:
kind create cluster
```

**Problem**: `error: You must be logged in to the server (Unauthorized)`
```bash
# Get credentials for your cluster
# For minikube:
minikube start

# For GKE:
gcloud container clusters get-credentials CLUSTER_NAME --zone=ZONE

# For EKS:
aws eks update-kubeconfig --region REGION --name CLUSTER_NAME

# For AKS:
az aks get-credentials --resource-group RG_NAME --name CLUSTER_NAME
```

**Problem**: `no space left on device` or pods stuck in Pending
```bash
# Check node resources
kubectl describe nodes

# For minikube, increase resources:
minikube stop
minikube start --memory=4096 --cpus=2 --disk-size=20g

# For Docker Desktop, increase resources in settings
```

#### Migration Issues

**Problem**: `type "userrole" already exists`
```bash
# Solution: Drop existing types and re-run migration
docker exec brownie-metadata-postgres psql -U brownie -d brownie_metadata -c "DROP TYPE IF EXISTS userrole CASCADE; DROP TYPE IF EXISTS incidentstatus CASCADE; DROP TYPE IF EXISTS incidentpriority CASCADE; DROP TYPE IF EXISTS agenttype CASCADE; DROP TYPE IF EXISTS configtype CASCADE; DROP TYPE IF EXISTS configstatus CASCADE;"
python3 -m alembic upgrade head
```

**Problem**: `connection to server at "localhost" (::1), port 5432 failed: Connection refused`
```bash
# Solution: Start PostgreSQL container
docker-compose up -d postgres
# Wait a few seconds for startup, then run migration
python3 -m alembic upgrade head
```

**Problem**: `Attribute name 'metadata' is reserved when using the Declarative API`
```bash
# Solution: Rename 'metadata' column to 'config_metadata' in your models
# This is already fixed in the current codebase
```

#### Database Connection Issues

**Problem**: Can't connect to database
```bash
# Check if container is running
docker ps | grep postgres

# Check container logs
docker logs brownie-metadata-postgres

# Restart container
docker-compose restart postgres
```

**Problem**: Database is locked or slow
```bash
# Check active connections
docker exec brownie-metadata-postgres psql -U brownie -d brownie_metadata -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Kill long-running queries (if needed)
docker exec brownie-metadata-postgres psql -U brownie -d brownie_metadata -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND pid <> pg_backend_pid();"
```

### Option 1: Docker Compose (Development)

1. Clone the repository:
```bash
git clone https://github.com/longyi-brownie/brownie-metadata-database.git
cd brownie-metadata-database
```

2. Start the services:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Redis on port 6379
- Application on port 8000
- Metrics endpoint on port 8001
- Prometheus on port 9090
- Grafana on port 3000

3. Run database migrations:
```bash
docker-compose exec migrate python -m alembic upgrade head
```

4. Access the services:
- Application: http://localhost:8000
- Metrics: http://localhost:8001/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Option 2: Kubernetes (Production)

#### Setting Up a Kubernetes Cluster

Before deploying to Kubernetes, you need a running cluster. Here are the most common options:

##### Local Development Clusters

**Minikube (Recommended for local development):**
```bash
# Install minikube
# macOS with Homebrew:
brew install minikube

# Or download from: https://minikube.sigs.k8s.io/docs/start/

# Start minikube with sufficient resources
minikube start --memory=4096 --cpus=2 --disk-size=20g

# Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server

# Verify cluster is running
kubectl get nodes
```

**Docker Desktop (macOS/Windows):**
```bash
# Enable Kubernetes in Docker Desktop settings
# Go to Settings > Kubernetes > Enable Kubernetes

# Verify cluster is running
kubectl get nodes
```

**Kind (Kubernetes in Docker):**
```bash
# Install kind
# macOS with Homebrew:
brew install kind

# Create cluster
kind create cluster --name brownie-metadata

# Verify cluster is running
kubectl get nodes
```

##### Cloud Clusters

**Google GKE:**
```bash
# Install gcloud CLI and authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create cluster
gcloud container clusters create brownie-metadata-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-medium

# Get credentials
gcloud container clusters get-credentials brownie-metadata-cluster --zone=us-central1-a
```

**Amazon EKS:**
```bash
# Install eksctl
# macOS with Homebrew:
brew install eksctl

# Create cluster
eksctl create cluster \
  --name brownie-metadata-cluster \
  --region=us-west-2 \
  --nodegroup-name=workers \
  --node-type=t3.medium \
  --nodes=3
```

**Azure AKS:**
```bash
# Install Azure CLI and login
az login

# Create resource group
az group create --name brownie-metadata-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group brownie-metadata-rg \
  --name brownie-metadata-cluster \
  --node-count 3 \
  --node-vm-size Standard_B2s

# Get credentials
az aks get-credentials --resource-group brownie-metadata-rg --name brownie-metadata-cluster
```

##### Verify Your Cluster

```bash
# Check cluster status
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check if you can create resources
kubectl auth can-i create pods
```

#### Using Raw Manifests
```bash
# Deploy everything
kubectl apply -k k8s/

# Check status
kubectl get pods -n brownie-metadata

# Access services
kubectl port-forward svc/brownie-metadata-app 8000:8000 -n brownie-metadata
kubectl port-forward svc/grafana 3000:3000 -n brownie-metadata
```

#### Using Helm Charts (Recommended)
```bash
# Install with Helm
helm install brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --create-namespace

# Scale easily
helm upgrade brownie-metadata-db ./k8s/helm \
  --set app.replicas=10 \
  --set database.patroni.replicas=5

# Check status
kubectl get pods -n brownie-metadata
```

**Kubernetes Features:**
- **High Availability**: Patroni PostgreSQL cluster with automatic failover
- **Read Replicas**: 3+ PostgreSQL instances for scaling reads
- **Connection Pooling**: PgBouncer for 1000+ concurrent connections
- **Auto-scaling**: HPA based on CPU/memory metrics
- **Monitoring**: Prometheus + Grafana with pre-built dashboards

### Local Development

1. Install dependencies:
```bash
pip install -e .
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

3. Start PostgreSQL and Redis locally

4. Run migrations:
```bash
python -m alembic upgrade head
```

5. Start the application:
```bash
python main.py
```

## Database Schema

### Core Tables

- **organizations** - Multi-tenant organizations
- **teams** - Teams within organizations
- **users** - Team members with RBAC roles
- **incidents** - Incident tracking with status and priority
- **agent_configs** - Brownie agent configurations
- **stats** - Metrics and analytics data

### Key Features

- **Multi-tenancy**: All tables include `org_id` for data isolation
- **Audit Logging**: Created/updated by tracking on mutations
- **Optimistic Concurrency**: Version columns for conflict resolution
- **Idempotency**: Idempotency keys for safe retries
- **Soft Deletes**: Soft delete support for data retention

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Configuration

### Environment Variables

See `env.example` for all available configuration options.

### Database Configuration

```python
DB_HOST=localhost
DB_PORT=5432
DB_NAME=brownie_metadata
DB_USER=brownie
DB_PASSWORD=brownie
```

### Logging Configuration

```python
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_PERFORMANCE=true
LOG_AUDIT=true
```

### Metrics Configuration

```python
METRICS_ENABLED=true
METRICS_PORT=8001
METRICS_TRACK_DATABASE_QUERIES=true
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run integration tests (API compatibility)
pytest tests/test_integration.py -v
```

### Integration Testing

**IMPORTANT**: Before making database schema changes, run integration tests to ensure the API doesn't break:

```bash
# Run integration tests to check API compatibility
pytest tests/test_integration.py::TestDatabaseAPIIntegration -v

# Run migration compatibility tests
pytest tests/test_integration.py::TestMigrationCompatibility -v
```

**What Integration Tests Check:**
- ✅ Database migrations can be applied successfully
- ✅ API can import all database models
- ✅ API can connect to the database
- ✅ API can query all tables
- ✅ API can create records in all tables
- ✅ API schemas match database models
- ✅ Migration creates all expected tables and indexes

**When to Run Integration Tests:**
- Before merging database changes
- After creating new migrations
- Before deploying to production
- When the API project is updated

## Monitoring

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- Database query performance
- Business metrics (incidents, users, teams)
- Error rates and response times
- Custom application metrics

### Logging

Structured JSON logs with:
- Request tracing
- Performance monitoring
- Security events
- Audit trails

### Grafana Dashboards

Pre-configured dashboards for:
- Database performance
- Application metrics
- Business KPIs
- Error monitoring

## Development

### Project Structure

```
src/
├── database/          # Database models and connection
├── logging/           # Logging configuration
├── metrics/           # Metrics collection
└── __init__.py

tests/                 # Test suite
alembic/              # Database migrations
k8s/                  # Kubernetes deployment
├── helm/             # Helm charts
├── *.yaml            # Raw Kubernetes manifests
└── README.md         # K8s deployment guide

monitoring/           # Prometheus and Grafana configs
scripts/              # Database initialization
docker-compose.yml    # Docker Compose setup
Dockerfile           # Application container
```

### Adding New Models

1. Create model in `src/database/models/`
2. Add to `src/database/models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "Add new model"`
4. Add tests in `tests/test_models.py`

### Adding Metrics

1. Add metric to `MetricsCollector` in `src/metrics/collector.py`
2. Update configuration in `src/metrics/config.py`
3. Add tests in `tests/test_metrics.py`

## Deployment

### Docker Compose (Development)

Perfect for local development and testing:

```bash
# Start all services
docker-compose up -d

# Scale application
docker-compose up -d --scale app=3

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Kubernetes (Production)

#### Raw Manifests
```bash
# Deploy everything
kubectl apply -k k8s/

# Check status
kubectl get pods -n brownie-metadata

# Scale application
kubectl scale deployment brownie-metadata-app --replicas=5 -n brownie-metadata

# Update image
kubectl set image deployment/brownie-metadata-app app=brownie-metadata-db:v1.1.0 -n brownie-metadata
```

#### Helm Charts (Recommended)
```bash
# Install
helm install brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --create-namespace

# Upgrade
helm upgrade brownie-metadata-db ./k8s/helm \
  --namespace brownie-metadata \
  --set app.replicas=10

# Uninstall
helm uninstall brownie-metadata-db --namespace brownie-metadata
```

### Production Considerations

#### High Availability
- **Patroni PostgreSQL cluster** with automatic failover
- **Read replicas** for scaling database reads
- **Connection pooling** with PgBouncer
- **Multi-zone deployment** for disaster recovery

#### Security
- **Kubernetes secrets** for sensitive data
- **Network policies** for traffic isolation
- **RBAC** for access control
- **Pod security contexts** for runtime security

#### Monitoring & Observability
- **Prometheus** for metrics collection
- **Grafana** dashboards for visualization
- **Structured logging** with audit trails
- **Health checks** and alerting

#### Scaling
- **Horizontal Pod Autoscaler** for automatic scaling
- **Database read replicas** for read-heavy workloads
- **Connection pooling** for high concurrency
- **Redis clustering** for session storage

### Architecture Comparison

| Feature | Docker Compose | Kubernetes |
|---------|---------------|------------|
| **Complexity** | Simple | Enterprise |
| **Scaling** | Manual | Automatic |
| **HA** | Single node | Multi-node |
| **Failover** | Manual | Automatic |
| **Monitoring** | Basic | Advanced |
| **Use Case** | Development | Production |

## License

[Add your license here]
