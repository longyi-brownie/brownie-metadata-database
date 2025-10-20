#!/bin/bash
set -e

# Make sure the script is executable
chmod +x /scripts/postgres-entrypoint.sh

# Copy certificates to a location where postgres user can own them
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

# Start PostgreSQL with the copied certificates
exec postgres \
    -c ssl=on \
    -c ssl_cert_file=/var/lib/postgresql/data/server.crt \
    -c ssl_key_file=/var/lib/postgresql/data/server.key \
    -c ssl_ca_file=/var/lib/postgresql/data/ca.crt \
    -c hba_file=/etc/postgresql/pg_hba.conf \
    "$@"
