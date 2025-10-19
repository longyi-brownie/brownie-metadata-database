# Runbook: Database Sharding for Enterprise

This runbook covers database sharding strategies and implementation for enterprise-scale Brownie Metadata Database deployments.

## TL;DR
- Team-based sharding recommended for multi-team organizations
- Time-based sharding for incident data archival and performance
- Hybrid sharding (team + time) for large enterprises
- Implement team shard router and cross-shard query patterns

---

## 1) Sharding Strategy Selection

### Team-Based Sharding (Recommended)
**Best for**: Large organizations with multiple teams
- **Partition Key**: `team_id`
- **Benefits**: Team data isolation, team-specific scaling, access control
- **Shard Count**: 3-10 shards initially, scale as needed
- **Use Case**: Each team gets their own shard for data isolation

### Time-Based Sharding
**Best for**: High-volume incident data with archival needs
- **Partition Key**: `created_at` or `incident_date`
- **Benefits**: Efficient archival, improved query performance, compliance
- **Shard Count**: Monthly or quarterly partitions
- **Use Case**: Separate active incidents from historical data

### Hybrid Sharding (Team + Time)
**Best for**: Large enterprises with high incident volume
- **Partition Key**: `team_id` + `created_at`
- **Benefits**: Both team isolation and time-based archival
- **Shard Count**: Multiple shards per team, partitioned by time
- **Use Case**: Team-specific shards with time-based partitioning

---

## 2) Team-Based Sharding Implementation

### Database Setup
```bash
# 1. Create team shard databases
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -c "
CREATE DATABASE brownie_metadata_team_1;
CREATE DATABASE brownie_metadata_team_2;
CREATE DATABASE brownie_metadata_team_3;
CREATE DATABASE brownie_metadata_team_4;
"

# 2. Create tables in each team shard
for shard in 1 2 3 4; do
  kubectl exec -n brownie-metadata deployment/postgres-primary -- psql -d brownie_metadata_team_$shard -c "
  CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE agent_configs (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    config_name VARCHAR(255) NOT NULL,
    config_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
  );
  "
done
```

### Shard Router Configuration
```yaml
# k8s/team-shard-router.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: team-shard-router
spec:
  replicas: 2
  selector:
    matchLabels:
      app: team-shard-router
  template:
    metadata:
      labels:
        app: team-shard-router
    spec:
      containers:
      - name: team-shard-router
        image: brownie-metadata-db:latest
        env:
        - name: TEAM_SHARD_COUNT
          value: "4"
        - name: TEAM_SHARD_1_CONNECTION
          value: "postgresql://brownie:password@postgres-primary:5432/brownie_metadata_team_1"
        - name: TEAM_SHARD_2_CONNECTION
          value: "postgresql://brownie:password@postgres-primary:5432/brownie_metadata_team_2"
        - name: TEAM_SHARD_3_CONNECTION
          value: "postgresql://brownie:password@postgres-primary:5432/brownie_metadata_team_3"
        - name: TEAM_SHARD_4_CONNECTION
          value: "postgresql://brownie:password@postgres-primary:5432/brownie_metadata_team_4"
```

### Team Shard Routing Logic
```python
# src/sharding/team_router.py
import hashlib
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

class TeamShardRouter:
    def __init__(self, team_shard_connections: dict):
        self.team_shard_connections = team_shard_connections
        self.shard_count = len(team_shard_connections)
        self.engines = {}
        
        # Initialize database connections
        for shard_id, connection_string in team_shard_connections.items():
            self.engines[shard_id] = create_engine(connection_string)
    
    def get_shard_for_team(self, team_id: int) -> str:
        """Route team to specific shard using consistent hashing"""
        shard_id = (team_id % self.shard_count) + 1
        return f"team_shard_{shard_id}"
    
    def get_engine_for_team(self, team_id: int) -> Engine:
        """Get database engine for team's shard"""
        shard_id = self.get_shard_for_team(team_id)
        return self.engines[shard_id]
    
    def get_all_engines(self) -> dict:
        """Get all shard engines for cross-shard queries"""
        return self.engines
    
    def get_teams_in_shard(self, shard_id: str) -> list:
        """Get all teams in a specific shard"""
        engine = self.engines[shard_id]
        with engine.connect() as conn:
            result = conn.execute("SELECT id, name FROM teams ORDER BY id")
            return [{"id": row.id, "name": row.name} for row in result]
```

---

## 3) Time-Based Sharding Implementation

### Partitioned Table Setup
```sql
-- Create partitioned incidents table
CREATE TABLE incidents (
    id SERIAL,
    team_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for current year
CREATE TABLE incidents_2024_01 PARTITION OF incidents
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE incidents_2024_02 PARTITION OF incidents
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE incidents_2024_03 PARTITION OF incidents
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Create indexes on partitions
CREATE INDEX idx_incidents_team_created_2024_01 ON incidents_2024_01 (team_id, created_at);
CREATE INDEX idx_incidents_team_created_2024_02 ON incidents_2024_02 (team_id, created_at);
CREATE INDEX idx_incidents_team_created_2024_03 ON incidents_2024_03 (team_id, created_at);
```

### Time-Based Router Configuration
```yaml
# k8s/time-shard-router.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: time-shard-router
spec:
  replicas: 2
  selector:
    matchLabels:
      app: time-shard-router
  template:
    metadata:
      labels:
        app: time-shard-router
    spec:
      containers:
      - name: time-shard-router
        image: brownie-metadata-db:latest
        env:
        - name: ACTIVE_PARTITION_MONTHS
          value: "6"  # Keep 6 months of active data
        - name: ARCHIVE_PARTITION_MONTHS
          value: "24"  # Keep 24 months of archived data
```

### Time-Based Routing Logic
```python
# src/sharding/time_router.py
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

class TimeShardRouter:
    def __init__(self, base_connection: str, active_months: int = 6, archive_months: int = 24):
        self.base_connection = base_connection
        self.active_months = active_months
        self.archive_months = archive_months
        self.engine = create_engine(base_connection)
    
    def get_partition_for_date(self, created_at: datetime) -> str:
        """Get partition name for specific date"""
        return f"incidents_{created_at.year}_{created_at.month:02d}"
    
    def get_active_partitions(self) -> list:
        """Get list of active partitions (last 6 months)"""
        partitions = []
        current_date = datetime.now()
        
        for i in range(self.active_months):
            target_date = current_date - timedelta(days=30 * i)
            partition_name = f"incidents_{target_date.year}_{target_date.month:02d}"
            partitions.append(partition_name)
        
        return partitions
    
    def get_archive_partitions(self) -> list:
        """Get list of archive partitions (6-24 months old)"""
        partitions = []
        current_date = datetime.now()
        
        for i in range(self.active_months, self.archive_months):
            target_date = current_date - timedelta(days=30 * i)
            partition_name = f"incidents_{target_date.year}_{target_date.month:02d}"
            partitions.append(partition_name)
        
        return partitions
    
    def should_archive_partition(self, partition_name: str) -> bool:
        """Check if partition should be moved to archive"""
        # Extract date from partition name
        year_month = partition_name.replace('incidents_', '')
        year, month = map(int, year_month.split('_'))
        partition_date = datetime(year, month, 1)
        
        cutoff_date = datetime.now() - timedelta(days=30 * self.active_months)
        return partition_date < cutoff_date
```

---

## 4) Time-Based Sharding Implementation

### Partitioned Table Setup
```sql
-- Create partitioned table
CREATE TABLE incidents (
    id SERIAL,
    organization_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE incidents_2024_01 PARTITION OF incidents
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE incidents_2024_02 PARTITION OF incidents
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE incidents_2024_03 PARTITION OF incidents
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Create indexes on partitions
CREATE INDEX idx_incidents_org_created_2024_01 ON incidents_2024_01 (organization_id, created_at);
CREATE INDEX idx_incidents_org_created_2024_02 ON incidents_2024_02 (organization_id, created_at);
CREATE INDEX idx_incidents_org_created_2024_03 ON incidents_2024_03 (organization_id, created_at);
```

### Automated Partition Management
```python
# src/sharding/partition_manager.py
from datetime import datetime, timedelta
from sqlalchemy import text

class PartitionManager:
    def __init__(self, engine):
        self.engine = engine
    
    def create_monthly_partition(self, year: int, month: int):
        """Create partition for specific month"""
        partition_name = f"incidents_{year}_{month:02d}"
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1)  # First day of next month
        
        query = f"""
        CREATE TABLE {partition_name} PARTITION OF incidents
        FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}');
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
    
    def drop_old_partitions(self, months_to_keep: int = 12):
        """Drop partitions older than specified months"""
        cutoff_date = datetime.now() - timedelta(days=months_to_keep * 30)
        
        # Get all partitions
        query = """
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'incidents_%' 
        AND tablename ~ '^incidents_[0-9]{4}_[0-9]{2}$'
        ORDER BY tablename;
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            partitions = result.fetchall()
            
            for schema, table in partitions:
                # Extract date from table name
                date_str = table.replace('incidents_', '')
                year, month = map(int, date_str.split('_'))
                partition_date = datetime(year, month, 1)
                
                if partition_date < cutoff_date:
                    drop_query = f"DROP TABLE {schema}.{table};"
                    conn.execute(text(drop_query))
                    conn.commit()
```

---

## 5) Cross-Shard Query Patterns

### Aggregation Queries
```python
# src/sharding/cross_shard_queries.py
from typing import List, Dict, Any
from sqlalchemy import text

class CrossShardQueries:
    def __init__(self, shard_router):
        self.shard_router = shard_router
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all shards"""
        total_incidents = 0
        total_organizations = 0
        total_users = 0
        
        for shard_id, engine in self.shard_router.get_all_engines().items():
            with engine.connect() as conn:
                # Get incident count
                result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
                incidents = result.scalar()
                total_incidents += incidents
                
                # Get organization count
                result = conn.execute(text("SELECT COUNT(*) FROM organizations"))
                orgs = result.scalar()
                total_organizations += orgs
                
                # Get user count
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                users = result.scalar()
                total_users += users
        
        return {
            'total_incidents': total_incidents,
            'total_organizations': total_organizations,
            'total_users': total_users
        }
    
    def search_across_shards(self, query: str) -> List[Dict[str, Any]]:
        """Search for incidents across all shards"""
        all_results = []
        
        for shard_id, engine in self.shard_router.get_all_engines().items():
            with engine.connect() as conn:
                search_query = text("""
                    SELECT id, organization_id, title, created_at
                    FROM incidents 
                    WHERE title ILIKE :query
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                
                result = conn.execute(search_query, {'query': f'%{query}%'})
                shard_results = result.fetchall()
                
                for row in shard_results:
                    all_results.append({
                        'id': row.id,
                        'organization_id': row.organization_id,
                        'title': row.title,
                        'created_at': row.created_at,
                        'shard': shard_id
                    })
        
        # Sort by created_at across all shards
        all_results.sort(key=lambda x: x['created_at'], reverse=True)
        return all_results[:100]  # Return top 100 results
```

### Data Consistency Patterns
```python
# src/sharding/consistency.py
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

class ShardConsistency:
    def __init__(self, shard_router):
        self.shard_router = shard_router
    
    def ensure_organization_exists(self, organization_id: int) -> bool:
        """Ensure organization exists in correct shard"""
        shard_id = self.shard_router.get_shard_for_organization(organization_id)
        engine = self.shard_router.get_engine_for_organization(organization_id)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM organizations WHERE id = :org_id"),
                {'org_id': organization_id}
            )
            count = result.scalar()
            return count > 0
    
    def create_organization_with_consistency(self, name: str, region: Optional[str] = None) -> int:
        """Create organization with proper shard placement"""
        # Generate organization ID
        organization_id = self._generate_organization_id()
        
        # Determine target shard
        if region:
            shard_id = self._get_shard_for_region(region)
        else:
            shard_id = self.shard_router.get_shard_for_organization(organization_id)
        
        engine = self.shard_router.engines[shard_id]
        
        with engine.connect() as conn:
            # Create organization
            result = conn.execute(
                text("INSERT INTO organizations (id, name) VALUES (:id, :name) RETURNING id"),
                {'id': organization_id, 'name': name}
            )
            conn.commit()
            return result.scalar()
```

---

## 6) Shard Migration Procedures

### Organization Migration
```bash
# 1. Identify organizations to migrate
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.sharding.migrator import ShardMigrator
migrator = ShardMigrator()
organizations = migrator.get_organizations_for_migration('shard_1', 'shard_2')
print(f'Organizations to migrate: {len(organizations)}')
"

# 2. Export organization data
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.sharding.migrator import ShardMigrator
migrator = ShardMigrator()
migrator.export_organization_data(org_id=123, from_shard='shard_1')
"

# 3. Import to target shard
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.sharding.migrator import ShardMigrator
migrator = ShardMigrator()
migrator.import_organization_data(org_id=123, to_shard='shard_2')
"

# 4. Verify migration
kubectl exec -n brownie-metadata deployment/brownie-metadata-app -- python -c "
from src.sharding.migrator import ShardMigrator
migrator = ShardMigrator()
migrator.verify_organization_migration(org_id=123, from_shard='shard_1', to_shard='shard_2')
"
```

### Zero-Downtime Migration
```python
# src/sharding/zero_downtime_migrator.py
class ZeroDowntimeMigrator:
    def __init__(self, shard_router):
        self.shard_router = shard_router
    
    def migrate_organization_zero_downtime(self, org_id: int, from_shard: str, to_shard: str):
        """Migrate organization with zero downtime"""
        # 1. Enable dual-write mode
        self._enable_dual_write(org_id, from_shard, to_shard)
        
        # 2. Copy existing data
        self._copy_existing_data(org_id, from_shard, to_shard)
        
        # 3. Verify data consistency
        self._verify_data_consistency(org_id, from_shard, to_shard)
        
        # 4. Switch reads to new shard
        self._switch_reads_to_new_shard(org_id, to_shard)
        
        # 5. Disable dual-write
        self._disable_dual_write(org_id, from_shard)
        
        # 6. Clean up old data
        self._cleanup_old_data(org_id, from_shard)
```

---

## 7) Monitoring and Alerting

### Shard Health Monitoring
```yaml
# k8s/shard-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shard-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'shard-health'
      static_configs:
      - targets: ['shard-router:8080']
      metrics_path: '/metrics'
      params:
        shard: ['shard_1', 'shard_2', 'shard_3', 'shard_4']
```

### Shard-Specific Alerts
```yaml
# k8s/shard-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: shard-alerts
spec:
  groups:
  - name: shard.rules
    rules:
    - alert: ShardDown
      expr: up{job="shard-health"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Shard {{ $labels.shard }} is down"
    
    - alert: ShardHighLatency
      expr: shard_query_duration_seconds{quantile="0.95"} > 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Shard {{ $labels.shard }} has high query latency"
    
    - alert: ShardUnbalancedLoad
      expr: abs(shard_query_rate - avg(shard_query_rate)) > avg(shard_query_rate) * 0.5
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "Shard {{ $labels.shard }} has unbalanced load"
```

---

## 8) Performance Optimization

### Shard-Specific Indexing
```sql
-- Optimize indexes for shard queries
CREATE INDEX CONCURRENTLY idx_incidents_org_created 
ON incidents (organization_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_users_org_email 
ON users (organization_id, email);

CREATE INDEX CONCURRENTLY idx_organizations_name 
ON organizations (name);
```

### Connection Pooling per Shard
```python
# src/sharding/connection_pooling.py
from sqlalchemy.pool import QueuePool

class ShardConnectionPool:
    def __init__(self, shard_connections: dict):
        self.pools = {}
        
        for shard_id, connection_string in shard_connections.items():
            self.pools[shard_id] = QueuePool(
                creator=lambda: create_engine(connection_string),
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
    
    def get_connection(self, shard_id: str):
        """Get connection from shard-specific pool"""
        return self.pools[shard_id].connect()
```

---

## 9) Backup and Recovery

### Shard-Specific Backups
```bash
# Backup individual shards
for shard in 1 2 3 4; do
  kubectl exec -n brownie-metadata deployment/postgres-primary -- pg_dump \
    -d brownie_metadata_shard_$shard \
    -f /backup/shard_$shard_$(date +%Y%m%d_%H%M%S).sql
done

# Restore individual shard
kubectl exec -n brownie-metadata deployment/postgres-primary -- psql \
  -d brownie_metadata_shard_1 \
  -f /backup/shard_1_20240115_120000.sql
```

### Cross-Shard Backup Coordination
```python
# src/sharding/backup_coordinator.py
class ShardBackupCoordinator:
    def __init__(self, shard_router, backup_manager):
        self.shard_router = shard_router
        self.backup_manager = backup_manager
    
    def create_consistent_backup(self):
        """Create consistent backup across all shards"""
        # 1. Stop writes to all shards
        self._stop_writes()
        
        # 2. Create backup of each shard
        shard_backups = {}
        for shard_id, engine in self.shard_router.get_all_engines().items():
            backup_name = f"shard_{shard_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shard_backups[shard_id] = self.backup_manager.create_backup(backup_name, engine)
        
        # 3. Resume writes
        self._resume_writes()
        
        return shard_backups
```

---

## 10) Definition of Done

- [ ] Sharding strategy selected and documented
- [ ] Shard databases created and configured
- [ ] Shard router deployed and tested
- [ ] Cross-shard query patterns implemented
- [ ] Migration procedures tested
- [ ] Monitoring and alerting configured
- [ ] Performance optimization completed
- [ ] Backup and recovery procedures tested
- [ ] Documentation updated
- [ ] Team trained on sharding procedures
