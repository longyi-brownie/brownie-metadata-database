# Brownie Metadata Database - Enterprise Monitoring

This directory contains enterprise-ready monitoring components for the Brownie Metadata Database service.

## 📊 Components

### Custom Metrics Sidecar
- **Location**: `metrics_sidecar/`
- **Purpose**: Collects custom application and database metrics
- **Port**: 9091
- **Metrics**: Database performance, Redis stats, business metrics

### Prometheus Configuration
- **File**: `prometheus.yml`
- **Purpose**: Metrics collection and alerting rules
- **Port**: 9090
- **Features**: Custom metrics scraping, alert rule evaluation

### Grafana Dashboards
- **Location**: `dashboards/`
- **Purpose**: Ready-to-use enterprise dashboards
- **Port**: 3000
- **Credentials**: admin/admin

### Alerting Rules
- **Location**: `alerts/`
- **Purpose**: Enterprise alerting rules for copy-paste
- **Types**: Database health, business metrics, performance

## 🚀 Quick Start

### Start Monitoring Stack
```bash
# Start all monitoring services
docker compose up -d

# Check status
docker compose ps

# Access services
curl http://localhost:9091/metrics  # Custom metrics
curl http://localhost:9090/targets  # Prometheus targets
curl http://localhost:3000/api/health  # Grafana health
```

### Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Custom Metrics**: http://localhost:9091/metrics

## 📈 Available Metrics

### Database Metrics
- `brownie_db_connections_total` - Active database connections
- `brownie_db_query_duration_seconds` - Query performance
- `brownie_db_query_errors_total` - Query error rates
- `brownie_db_size_bytes` - Database size
- `brownie_table_size_bytes` - Table sizes

### Redis Metrics
- `brownie_redis_memory_usage_bytes` - Memory usage
- `brownie_redis_hit_rate` - Cache hit rate
- `brownie_redis_connected_clients` - Connected clients

### Business Metrics
- `brownie_organizations_total` - Total organizations
- `brownie_teams_total` - Total teams
- `brownie_users_total` - Total users
- `brownie_incidents_total` - Total incidents
- `brownie_agent_configs_total` - Total agent configurations

## 🚨 Alerting Rules

### Database Health Alerts
- **DatabaseDown**: Database unreachable
- **HighDatabaseConnections**: Too many active connections
- **DatabaseDiskSpaceLow**: Low disk space
- **DatabaseQueryErrors**: High query error rate

### Business Metrics Alerts
- **NoNewOrganizations**: No new organizations in 24h
- **HighIncidentVolume**: High incident creation rate
- **LowAgentConfigCreation**: Low agent config creation

## 📊 Enterprise Dashboards

### Database Overview Dashboard
- **File**: `dashboards/database-overview.json`
- **Metrics**: Connection pools, query performance, table sizes
- **Use Case**: Database health monitoring

### Business Metrics Dashboard
- **File**: `dashboards/business-metrics.json`
- **Metrics**: User growth, incident trends, team activity
- **Use Case**: Business intelligence and reporting

## 🔧 Configuration

### Custom Metrics Collection
The metrics sidecar automatically collects:
- Database connection stats every 30 seconds
- Redis performance metrics every 30 seconds
- Business metrics every 30 seconds

### Prometheus Scraping
- **Interval**: 15 seconds
- **Retention**: 200 hours
- **Targets**: Custom metrics sidecar

### Grafana Provisioning
- **Auto-provisioning**: Enabled
- **Dashboard refresh**: 10 seconds
- **Datasource**: Prometheus (auto-configured)

## 🏢 Enterprise Deployment

### For Customer Environments
1. **Copy monitoring directory** to customer environment
2. **Update Prometheus targets** in `prometheus.yml`
3. **Customize dashboards** in `dashboards/`
4. **Configure alerting** in `alerts/`
5. **Deploy with Kubernetes** using `k8s/monitoring.yaml`

### Customization
- **Metrics**: Modify `metrics_sidecar/__main__.py`
- **Dashboards**: Edit JSON files in `dashboards/`
- **Alerts**: Update YAML files in `alerts/`
- **Prometheus**: Configure `prometheus.yml`

## 📚 Documentation

- **[Backup Procedures](BACKUP.md)** - Database backup and restore
- **[Developer Quick Reference](DEVELOPER_QUICK_REFERENCE.md)** - Development setup
- **[Runbooks](../runbooks/)** - Operational procedures

## 🔗 Related Files

- `../docker-compose.yml` - Complete stack with monitoring
- `../k8s/monitoring.yaml` - Kubernetes monitoring deployment
- `../requirements-metrics.txt` - Metrics sidecar dependencies
- `../Dockerfile.metrics` - Metrics sidecar container
