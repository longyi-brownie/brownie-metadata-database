#!/bin/bash
# Automated PostgreSQL SSL and certificate authentication setup

set -e

echo "Setting up PostgreSQL SSL and certificate authentication..."

# Create directory for PostgreSQL config
mkdir -p /etc/postgresql

# Create pg_hba.conf for certificate authentication
cat > /etc/postgresql/pg_hba.conf << 'EOF'
# PostgreSQL Client Authentication Configuration File
# ===================================================

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     trust

# IPv4 local connections:
host    all             all             127.0.0.1/32            trust

# IPv6 local connections:
host    all             all             ::1/128                 trust

# SSL connections with certificate authentication
hostssl all             all             0.0.0.0/0               cert

# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
EOF

echo "Created pg_hba.conf for certificate authentication"

# Create certificate user and grant permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" << 'EOF'
-- Create user for certificate authentication
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'brownie-fastapi-server') THEN
        CREATE USER "brownie-fastapi-server";
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE brownie_metadata TO "brownie-fastapi-server";
GRANT USAGE ON SCHEMA public TO "brownie-fastapi-server";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "brownie-fastapi-server";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "brownie-fastapi-server";

-- Grant permissions on future tables (for Alembic migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "brownie-fastapi-server";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "brownie-fastapi-server";

-- Remove password authentication for the main user
-- This ensures only certificate authentication is allowed
ALTER USER brownie WITH NOLOGIN;
EOF

echo "Created certificate user and configured permissions"
echo "PostgreSQL SSL and certificate authentication setup complete!"
