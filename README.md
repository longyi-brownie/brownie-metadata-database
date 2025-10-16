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
```

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
