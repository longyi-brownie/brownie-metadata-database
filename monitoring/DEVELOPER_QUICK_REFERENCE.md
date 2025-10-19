# Developer Quick Reference

## 🚀 Essential Commands

### Database Setup
```bash
# Start database
docker-compose up -d postgres

# Run migrations
python3 -m alembic upgrade head

# Connect to database
docker exec -it brownie-metadata-postgres psql -U brownie -d brownie_metadata
```

### Development Workflow
```bash
# 1. Pull latest changes
git pull

# 2. Run migrations (if any)
python3 -m alembic upgrade head

# 3. Start services
docker-compose up -d

# 4. Run tests
pytest

# 5. Check logs
docker-compose logs -f
```

## 🔧 Common Tasks

### Create New Migration
```bash
# After modifying models
python3 -m alembic revision --autogenerate -m "Add new field to users table"
python3 -m alembic upgrade head
```

### Debug Database
```sql
-- List tables
\dt

-- Check table structure
\d organizations

-- See sample data
SELECT * FROM organizations LIMIT 5;

-- Check migration status
SELECT * FROM alembic_version;
```

### Reset Database
```bash
# Nuclear option - reset everything
docker-compose down -v
docker-compose up -d postgres
python3 -m alembic upgrade head
```

## 🐛 Quick Fixes

### Migration Errors
```bash
# ENUM already exists
docker exec brownie-metadata-postgres psql -U brownie -d brownie_metadata -c "DROP TYPE IF EXISTS userrole CASCADE; DROP TYPE IF EXISTS incidentstatus CASCADE; DROP TYPE IF EXISTS incidentpriority CASCADE; DROP TYPE IF EXISTS agenttype CASCADE; DROP TYPE IF EXISTS configtype CASCADE; DROP TYPE IF EXISTS configstatus CASCADE;"

# Connection refused
docker-compose up -d postgres
sleep 5
python3 -m alembic upgrade head
```

### Container Issues
```bash
# Restart everything
docker-compose restart

# Check logs
docker-compose logs postgres
docker-compose logs app

# Rebuild containers
docker-compose up --build
```

## 📊 Useful Queries

### Check Data
```sql
-- Count records per table
SELECT 'organizations' as table_name, COUNT(*) as count FROM organizations
UNION ALL
SELECT 'teams', COUNT(*) FROM teams
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL
SELECT 'configs', COUNT(*) FROM configs;

-- Check config data
SELECT name, config_type, status, is_active FROM configs;
```

### Performance
```sql
-- Table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- Active connections
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';
```

## 🏗️ Project Structure

```
brownie-metadata-database/
├── src/
│   ├── database/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── config.py        # Database config
│   │   └── connection.py    # Connection management
│   ├── logging/             # Structured logging
│   └── metrics/             # Prometheus metrics
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── k8s/                     # Kubernetes manifests
└── docker-compose.yml       # Local development
```

## 🔗 Key Files

- **Models**: `src/database/models/`
- **Migrations**: `alembic/versions/`
- **Config**: `src/database/config.py`
- **Docker**: `docker-compose.yml`
- **K8s**: `k8s/`

## 📝 Notes

- Always run migrations after pulling code changes
- Use `docker-compose exec` for one-off commands
- Check logs when things go wrong
- Test migrations on a copy of production data
- Use transactions for data changes
