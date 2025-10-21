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
    # Copy the pg_hba.conf from the mounted volume to the data directory
    if [ -f "/etc/postgresql/pg_hba.conf" ]; then
        cp /etc/postgresql/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf
        chown postgres:postgres /var/lib/postgresql/data/pg_hba.conf
        chmod 644 /var/lib/postgresql/data/pg_hba.conf
        echo "Copied pg_hba.conf from mounted volume"
    else
        echo "WARNING: /etc/postgresql/pg_hba.conf not found, using default"
    fi
    echo "=== Internal certificate setup completed ==="
}

# If this is the first argument and it's 'postgres', or if no arguments are provided (default postgres command)
if [ "$1" = 'postgres' ] || [ $# -eq 0 ]; then
    echo "=== Starting PostgreSQL server with SSL ==="

    PGDATA_DIR="${PGDATA:-/var/lib/postgresql/data}"

    # Check if database is already initialized
    if [ ! -f "${PGDATA_DIR}/PG_VERSION" ]; then
        echo "=== Database not initialized, running default entrypoint for setup ==="

        # Run the default entrypoint to perform initialization tasks
        /usr/local/bin/docker-entrypoint.sh postgres &
        POSTGRES_PID=$!

        # Wait for PostgreSQL to become ready which indicates initialization has completed
        echo "=== Waiting for PostgreSQL initialization to complete ==="
        until su-exec postgres pg_isready -U postgres -d postgres >/dev/null 2>&1; do
            if ! kill -0 ${POSTGRES_PID} >/dev/null 2>&1; then
                echo "*** PostgreSQL initialization process exited unexpectedly ***"
                wait ${POSTGRES_PID}
            fi
            sleep 1
        done

        echo "=== Stopping temporary PostgreSQL instance after initialization ==="
        su-exec postgres pg_ctl -D "${PGDATA_DIR}" -m fast -w stop

        # Ensure the background process has fully exited
        wait ${POSTGRES_PID}
    fi

    echo "=== Copying certificates and pg_hba.conf ==="
    copy_certificates
    setup_internal_certs

    # Start PostgreSQL with SSL configuration as postgres user
    echo "=== Starting PostgreSQL with SSL configuration as postgres user ==="
    exec su-exec postgres postgres \
        -c ssl=on \
        -c ssl_cert_file=${PGDATA_DIR}/server.crt \
        -c ssl_key_file=${PGDATA_DIR}/server.key \
        -c ssl_ca_file=${PGDATA_DIR}/ca.crt \
        -c hba_file=${PGDATA_DIR}/pg_hba.conf
else
    echo "=== Passing through to original entrypoint: $@ ==="
    # For other commands (like initdb), just pass through to the original entrypoint
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi
