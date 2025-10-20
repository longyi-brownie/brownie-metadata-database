#!/bin/bash
set -e

# Function to copy certificates with proper ownership
copy_certificates() {
    if [ -f "/var/lib/postgresql/server.crt" ]; then
        cp /var/lib/postgresql/server.crt /var/lib/postgresql/data/server.crt
        chown postgres:postgres /var/lib/postgresql/data/server.crt
        chmod 644 /var/lib/postgresql/data/server.crt
    fi

    if [ -f "/var/lib/postgresql/server.key" ]; then
        cp /var/lib/postgresql/server.key /var/lib/postgresql/data/server.key
        chown postgres:postgres /var/lib/postgresql/data/server.key
        chmod 600 /var/lib/postgresql/data/server.key
    fi

    if [ -f "/var/lib/postgresql/ca.crt" ]; then
        cp /var/lib/postgresql/ca.crt /var/lib/postgresql/data/ca.crt
        chown postgres:postgres /var/lib/postgresql/data/ca.crt
        chmod 644 /var/lib/postgresql/data/ca.crt
    fi
}

# If this is the first argument and it's 'postgres', we're starting the server
if [ "$1" = 'postgres' ]; then
    # Copy certificates before starting PostgreSQL
    copy_certificates
    
    # Start PostgreSQL with SSL configuration
    exec /usr/local/bin/docker-entrypoint.sh postgres \
        -c ssl=on \
        -c ssl_cert_file=/var/lib/postgresql/data/server.crt \
        -c ssl_key_file=/var/lib/postgresql/data/server.key \
        -c ssl_ca_file=/var/lib/postgresql/data/ca.crt \
        -c hba_file=/etc/postgresql/pg_hba.conf
else
    # For other commands (like initdb), just pass through to the original entrypoint
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi
