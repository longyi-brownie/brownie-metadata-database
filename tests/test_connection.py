"""Test database connection and session management."""

import pytest
from sqlalchemy.exc import OperationalError

from src.database.config import DatabaseSettings
from src.database.connection import DatabaseManager, get_database_manager


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_create_database_manager(self):
        """Test creating a database manager."""
        settings = DatabaseSettings()
        manager = DatabaseManager(settings)

        assert manager.settings == settings
        assert manager._engine is None
        assert manager._session_factory is None

    def test_create_engine(self):
        """Test creating database engine."""
        settings = DatabaseSettings(
            host="definitely-does-not-exist.invalid",  # Invalid hostname that won't resolve
            port=5432,
            name="test_db",
            user="test",
            password="test",
        )
        manager = DatabaseManager(settings)

        # This will fail with a nonexistent host
        engine = manager.create_engine()
        with pytest.raises(OperationalError):
            # Actually try to connect to trigger the error
            with engine.connect() as conn:
                conn.execute("SELECT 1")

    def test_get_database_manager_singleton(self):
        """Test that get_database_manager returns a singleton."""
        manager1 = get_database_manager()
        manager2 = get_database_manager()

        assert manager1 is manager2


class TestDatabaseSettings:
    """Test DatabaseSettings class."""

    def test_database_url(self):
        """Test database URL generation."""
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            name="test_db",
            user="test",
            password="test",
        )

        expected_url = "postgresql://test:test@localhost:5432/test_db"
        assert settings.database_url == expected_url

    def test_async_database_url(self):
        """Test async database URL generation."""
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            name="test_db",
            user="test",
            password="test",
        )

        expected_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        assert settings.async_database_url == expected_url

    def test_default_values(self):
        """Test default configuration values."""
        settings = DatabaseSettings()

        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.name == "brownie_metadata"
        assert settings.user == "brownie"
        assert settings.password == "brownie"
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
