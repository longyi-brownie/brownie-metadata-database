#!/bin/bash
set -e

echo "=== PostgreSQL entrypoint script started ==="
echo "Arguments: $@"
echo "First argument: '$1'"
echo "Number of arguments: $#"

# Make sure the script is executable
chmod +x /scripts/postgres-entrypoint.sh

# Function to copy certificates with proper ownership
copy_certificates() {
    echo "=== Copying certificates with proper ownership ==="
    if [ -f "/var/lib/postgresql/server.crt" ]; then
        cp /var/lib/postgresql/server.crt /var/lib/postgresql/data/server.crt
        chown postgres:postgres /var/lib/postgresql/data/server.crt
        chmod 644 /var/lib/postgresql/data/server.crt
        echo "Copied server.crt"
    fi

    if [ -f "/var/lib/postgresql/server.key" ]; then
        cp /var/lib/postgresql/server.key /var/lib/postgresql/data/server.key
        chown postgres:postgres /var/lib/postgresql/data/server.key
        chmod 600 /var/lib/postgresql/data/server.key
        echo "Copied server.key"
    fi

    if [ -f "/var/lib/postgresql/ca.crt" ]; then
        cp /var/lib/postgresql/ca.crt /var/lib/postgresql/data/ca.crt
        chown postgres:postgres /var/lib/postgresql/data/ca.crt
        chmod 644 /var/lib/postgresql/data/ca.crt
        echo "Copied ca.crt"
    fi
    echo "=== Certificate copying completed ==="
}

# Function to set up certificates for internal connections
setup_internal_certs() {
    echo "=== Setting up certificates for internal connections ==="
    # Create a custom pg_hba.conf that allows internal connections without SSL
    # This allows internal services to connect without SSL certificates
    cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# PostgreSQL Client Authentication Configuration File
# ===================================================

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     trust

# IPv4 local connections (localhost only, no password)
host    all             all             127.0.0.1/32            trust

# IPv6 local connections (localhost only, no password)
host    all             all             ::1/128                 trust

# Allow internal Docker network connections without SSL
host    all             all             172.0.0.0/8             trust

# SSL connections with certificate authentication (REQUIRED for external connections)
hostssl all             all             0.0.0.0/0               cert

# Deny all other connections
host    all             all             0.0.0.0/0               reject

# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
EOF
    echo "=== Internal certificate setup completed ==="
}

# If this is the first argument and it's 'postgres', or if no arguments are provided (default postgres command)
if [ "$1" = 'postgres' ] || [ $# -eq 0 ]; then
    echo "=== Starting PostgreSQL server with SSL ==="
    
    # Check if database is already initialized
    if [ ! -f "/var/lib/postgresql/data/PG_VERSION" ]; then
        echo "=== Database not initialized, letting PostgreSQL initialize first ==="
        # Let PostgreSQL initialize the database first
        /usr/local/bin/docker-entrypoint.sh postgres &
        POSTGRES_PID=$!
        
        # Wait for PostgreSQL to initialize
        echo "=== Waiting for PostgreSQL initialization to complete ==="
        wait $POSTGRES_PID
        
        # Now copy certificates after initialization
        echo "=== PostgreSQL initialization complete, copying certificates ==="
        copy_certificates
        setup_internal_certs
        
        # Start PostgreSQL with SSL configuration as postgres user
        echo "=== Starting PostgreSQL with SSL configuration as postgres user ==="
        exec su-exec postgres postgres \
            -c ssl=on \
            -c ssl_cert_file=/var/lib/postgresql/data/server.crt \
            -c ssl_key_file=/var/lib/postgresql/data/server.key \
            -c ssl_ca_file=/var/lib/postgresql/data/ca.crt \
            -c hba_file=/var/lib/postgresql/data/pg_hba.conf
    else
        echo "=== Database already initialized, copying certificates and starting with SSL ==="
        # Database already exists, just copy certificates and start
        copy_certificates
        setup_internal_certs
        
        # Start PostgreSQL with SSL configuration as postgres user
        echo "=== Starting PostgreSQL with SSL configuration as postgres user ==="
        exec su-exec postgres postgres \
            -c ssl=on \
            -c ssl_cert_file=/var/lib/postgresql/data/server.crt \
            -c ssl_key_file=/var/lib/postgresql/data/server.key \
            -c ssl_ca_file=/var/lib/postgresql/data/ca.crt \
            -c hba_file=/var/lib/postgresql/data/pg_hba.conf
    fi
else
    echo "=== Passing through to original entrypoint: $@ ==="
    # For other commands (like initdb), just pass through to the original entrypoint
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi
