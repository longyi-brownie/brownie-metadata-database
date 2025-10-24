"""Integration tests for database schema compatibility."""

import os
import socket
import subprocess

# Add src to path for imports
import sys
from pathlib import Path

import pytest

from brownie_metadata_db.database.base import Base as DatabaseBase


def _is_postgres_available():
    """Check if PostgreSQL is available on localhost:5432."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 5432))
        sock.close()
        if result != 0:
            return False

        # Try to connect with SSL first, then without SSL
        try:
            import psycopg2

            # Try SSL connection with certificates first
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="brownie_metadata",
                    user="brownie-fastapi-server",
                    sslmode="verify-full",  # Use verify-full for enterprise-level security
                    sslcert="dev-certs/client.crt",
                    sslkey="dev-certs/client.key",
                    sslrootcert="dev-certs/ca.crt",
                )
                conn.close()
                return True
            except Exception:
                # If SSL with certificates fails, return False (no fallback to password)
                return False
        except Exception:
            return False
    except Exception:
        return False


def _start_postgres_if_needed():
    """Start PostgreSQL container if it's not running."""
    try:
        # Check if PostgreSQL is already running
        if _is_postgres_available():
            return True

        # Start PostgreSQL container
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "postgres"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode != 0:
            print(f"Failed to start PostgreSQL: {result.stderr}")
            return False

        # Wait for PostgreSQL to be ready
        import time

        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if _is_postgres_available():
                return True

        return False
    except Exception as e:
        print(f"Error starting PostgreSQL: {e}")
        return False


class TestDatabaseSchema:
    """Test that database schema works correctly."""

    def test_can_import_models(self):
        """Test that we can import all database models."""
        try:
            # Test importing models from the database project
            from database.models import (
                AgentConfig,
                AgentType,
                Config,
                Incident,
                IncidentPriority,
                IncidentStatus,
                Organization,
                Stats,
                Team,
                User,
                UserRole,
            )

            # Verify models exist
            assert AgentConfig is not None
            assert AgentType is not None
            assert Config is not None
            assert Incident is not None
            assert IncidentPriority is not None
            assert IncidentStatus is not None
            assert Organization is not None
            assert Stats is not None
            assert Team is not None
            assert User is not None
            assert UserRole is not None

        except ImportError as e:
            pytest.fail(f"Failed to import database models: {e}")


def test_database_migration_works():
    """Test that database migrations can be applied successfully."""
    # Start PostgreSQL if needed
    if not _start_postgres_if_needed():
        pytest.skip("PostgreSQL not available and could not be started")

    # Use our existing database setup with flexible SSL configuration
    env = os.environ.copy()

    # Use certificate authentication (no passwords)
    # Using 'verify-full' for enterprise-level security with proper certificate validation
    env.update(
        {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "brownie_metadata",
            "DB_USER": "brownie-fastapi-server",
            "DB_PASSWORD": "",  # No password - use certificate authentication
            "DB_SSL_MODE": "verify-full",
            "CERT_DIR": "dev-certs",
        }
    )

    # Set the environment variable for the current process as well
    os.environ["CERT_DIR"] = "dev-certs"

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
