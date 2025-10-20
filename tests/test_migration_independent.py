"""Independent migration test that starts its own Docker container."""

import os
import subprocess
import time
from pathlib import Path

import pytest


def test_database_migration_with_independent_docker():
    """Test that database migrations work with an independent Docker container."""
    # Start a fresh PostgreSQL container for this test
    container_name = "brownie-migration-test"

    try:
        # Clean up any existing container
        subprocess.run(
            ["docker", "rm", "-f", container_name], capture_output=True, check=False
        )

        # Start a new PostgreSQL container
        start_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-e",
            "POSTGRES_DB=brownie_metadata",
            "-e",
            "POSTGRES_USER=brownie-fastapi-server",
            "-e",
            "POSTGRES_PASSWORD=test_password",
            "-p",
            "5433:5432",  # Use different port to avoid conflicts
            "postgres:16",
        ]

        result = subprocess.run(start_cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()

        # Wait for PostgreSQL to be ready
        print("Waiting for PostgreSQL to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                check_cmd = [
                    "docker",
                    "exec",
                    container_name,
                    "pg_isready",
                    "-U",
                    "brownie-fastapi-server",
                    "-d",
                    "brownie_metadata",
                ]
                result = subprocess.run(
                    check_cmd, capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    print("PostgreSQL is ready!")
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            pytest.fail("PostgreSQL container failed to start within 30 seconds")

        # Set up environment for migration
        env = os.environ.copy()
        env.update(
            {
                "DB_HOST": "localhost",
                "DB_PORT": "5433",  # Use the test container port
                "DB_NAME": "brownie_metadata",
                "DB_USER": "brownie-fastapi-server",
                "DB_PASSWORD": "test_password",
                "DB_SSL_MODE": "disable",  # Disable SSL for test container
                "CERT_DIR": "",  # No certificates needed for test
            }
        )

        # Run migration
        print("Running database migration...")
        result = subprocess.run(
            ["python3", "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Migration failed: {result.stderr}"
        print(f"Migration output: {result.stdout}")

        # Verify migration worked by checking if tables exist
        verify_cmd = [
            "docker",
            "exec",
            container_name,
            "psql",
            "-U",
            "brownie-fastapi-server",
            "-d",
            "brownie_metadata",
            "-c",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
        ]

        result = subprocess.run(verify_cmd, capture_output=True, text=True, check=True)
        print(f"Tables created: {result.stdout}")

        # Check for key tables
        assert "organizations" in result.stdout
        assert "teams" in result.stdout
        assert "users" in result.stdout
        assert "incidents" in result.stdout

    finally:
        # Clean up the container
        subprocess.run(
            ["docker", "rm", "-f", container_name], capture_output=True, check=False
        )
