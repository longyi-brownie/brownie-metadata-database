"""Test database connection and session management."""

import pytest
from sqlalchemy.exc import OperationalError

from database.connection import DatabaseManager, get_database_manager
from database.config import DatabaseSettings


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
            host="localhost",
            port=5432,
            name="test_db",
            user="test",
            password="test",
        )
        manager = DatabaseManager(settings)
        
        # This will fail without a real database, but we can test the configuration
        with pytest.raises(OperationalError):
            manager.create_engine()
    
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
