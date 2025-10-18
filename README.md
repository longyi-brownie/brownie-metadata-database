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
