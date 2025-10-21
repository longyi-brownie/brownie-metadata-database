#!/bin/bash
set -euo pipefail

echo "=== PostgreSQL entrypoint wrapper started ==="
echo "Arguments: $*"
echo "Number of arguments: $#"

PGDATA=${PGDATA:-/var/lib/postgresql/data}
INIT_HOOK="/docker-entrypoint-initdb.d/00-configure-internal-auth.sh"

# Ensure the script itself remains executable when mounted as a volume
chmod +x /scripts/postgres-entrypoint.sh || true

# Copy certificates and pg_hba.conf into the data directory with correct ownership
configure_runtime_files() {
    echo "=== Configuring PostgreSQL runtime files in ${PGDATA} ==="

    if [ -f "/var/lib/postgresql/server.crt" ]; then
        cp /var/lib/postgresql/server.crt "${PGDATA}/server.crt"
        chown postgres:postgres "${PGDATA}/server.crt"
        chmod 644 "${PGDATA}/server.crt"
        echo "Copied server.crt"
    else
        echo "WARNING: /var/lib/postgresql/server.crt not found"
    fi

    if [ -f "/var/lib/postgresql/server.key" ]; then
        cp /var/lib/postgresql/server.key "${PGDATA}/server.key"
        chown postgres:postgres "${PGDATA}/server.key"
        chmod 600 "${PGDATA}/server.key"
        echo "Copied server.key"
    else
        echo "WARNING: /var/lib/postgresql/server.key not found"
    fi

    if [ -f "/var/lib/postgresql/ca.crt" ]; then
        cp /var/lib/postgresql/ca.crt "${PGDATA}/ca.crt"
        chown postgres:postgres "${PGDATA}/ca.crt"
        chmod 644 "${PGDATA}/ca.crt"
        echo "Copied ca.crt"
    else
        echo "WARNING: /var/lib/postgresql/ca.crt not found"
    fi

    if [ -f "/etc/postgresql/pg_hba.conf" ]; then
        cp /etc/postgresql/pg_hba.conf "${PGDATA}/pg_hba.conf"
        chown postgres:postgres "${PGDATA}/pg_hba.conf"
        chmod 644 "${PGDATA}/pg_hba.conf"
        echo "Installed pg_hba.conf"
    else
        echo "WARNING: /etc/postgresql/pg_hba.conf not found; default authentication will be used"
    fi

    echo "=== Runtime file configuration complete ==="
}

# Create a hook script that will run during the initial database setup
ensure_init_hook() {
    if [ -f "${INIT_HOOK}" ]; then
        return
    fi

    echo "=== Installing initialization hook for certificate and pg_hba setup ==="
    cat <<'HOOK' >"${INIT_HOOK}"
#!/bin/bash
set -euo pipefail

PGDATA=${PGDATA:-/var/lib/postgresql/data}

copy_file() {
    local source="$1"
    local dest="$2"
    local mode="$3"

    if [ -f "${source}" ]; then
        cp "${source}" "${dest}"
        chown postgres:postgres "${dest}"
        chmod "${mode}" "${dest}"
        echo "Initialized $(basename "${dest}") from ${source}"
    else
        echo "WARNING: ${source} not found during initialization"
    fi
}

copy_file "/var/lib/postgresql/server.crt" "${PGDATA}/server.crt" 644
copy_file "/var/lib/postgresql/server.key" "${PGDATA}/server.key" 600
copy_file "/var/lib/postgresql/ca.crt" "${PGDATA}/ca.crt" 644

if [ -f "/etc/postgresql/pg_hba.conf" ]; then
    cp "/etc/postgresql/pg_hba.conf" "${PGDATA}/pg_hba.conf"
    chown postgres:postgres "${PGDATA}/pg_hba.conf"
    chmod 644 "${PGDATA}/pg_hba.conf"
    echo "Initialized pg_hba.conf"
else
    echo "WARNING: /etc/postgresql/pg_hba.conf not found during initialization"
fi
HOOK

    chmod +x "${INIT_HOOK}"
}

if [ $# -eq 0 ]; then
    set -- postgres
fi

if [ "$1" = 'postgres' ]; then
    if [ ! -s "${PGDATA}/PG_VERSION" ]; then
        # Database is not initialized yet; install the init hook so the official entrypoint
        # copies certificates and authentication configuration at the correct time.
        ensure_init_hook
    else
        # Database already exists, so update certificates and pg_hba before handing control over.
        configure_runtime_files
    fi
fi

echo "=== Handing control to the official PostgreSQL entrypoint ==="
exec /usr/local/bin/docker-entrypoint.sh "$@"
