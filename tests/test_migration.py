"""Test that database migrations work correctly."""

import os
import subprocess
import socket
from pathlib import Path

import pytest


def _is_postgres_available():
    """Check if PostgreSQL is available on localhost:5432."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 5432))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.mark.skipif(
    not _is_postgres_available(), reason="PostgreSQL not available on localhost:5432"
)
def test_database_migration_works():
    """Test that database migrations can be applied successfully."""
    # Use our existing database setup with proper SSL configuration
    env = os.environ.copy()
    env.update(
        {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "brownie_metadata",
            "DB_USER": "brownie-fastapi-server",
            "DB_PASSWORD": "",  # No password needed with certificates
            "DB_SSL_MODE": "require",
            "CERT_DIR": "dev-certs",  # Use our dev certificates
        }
    )

    # Run migration
    result = subprocess.run(
        ["python3", "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parent.parent,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Migration failed: {result.stderr}"
    print(f"Migration output: {result.stdout}")
