"""Integration tests for database schema compatibility."""

import os
import subprocess

# Add src to path for imports
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.base import Base as DatabaseBase


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
