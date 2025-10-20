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

# If this is the first argument and it's 'postgres', or if no arguments are provided (default postgres command)
if [ "$1" = 'postgres' ] || [ $# -eq 0 ]; then
    echo "=== Starting PostgreSQL server with SSL ==="
    # Copy certificates before starting PostgreSQL
    copy_certificates
    
    # Start PostgreSQL with SSL configuration - use exec to replace the shell process
    echo "=== Executing PostgreSQL with SSL configuration ==="
    exec /usr/local/bin/docker-entrypoint.sh postgres \
        -c ssl=on \
        -c ssl_cert_file=/var/lib/postgresql/data/server.crt \
        -c ssl_key_file=/var/lib/postgresql/data/server.key \
        -c ssl_ca_file=/var/lib/postgresql/data/ca.crt \
        -c hba_file=/etc/postgresql/pg_hba.conf
else
    echo "=== Passing through to original entrypoint: $@ ==="
    # For other commands (like initdb), just pass through to the original entrypoint
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi
