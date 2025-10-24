"""Database connection and session management."""

import os
from typing import Optional, Union

import structlog
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from brownie_metadata_db.certificates import CertificateValidator, cert_config

from .config import DatabaseSettings

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None

    def create_engine(self) -> Engine:
        """Create and configure the database engine."""
        if self._engine is not None:
            return self._engine

        # Build database URL
        database_url = self.settings.database_url

        # Add SSL parameters for certificate authentication
        connect_args = {}
        ssl_mode = os.getenv("DB_SSL_MODE", "verify-full")

        if ssl_mode in ["require", "verify-ca", "verify-full", "prefer"]:
            connect_args["sslmode"] = ssl_mode

            # Add certificate paths if available
            cert_paths = cert_config.get_client_cert_paths()
            client_cert = cert_paths["client_cert"]
            client_key = cert_paths["client_key"]
            ca_cert = cert_paths["ca_cert"]

            # Validate certificates if they exist
            if os.path.exists(client_cert) and os.path.exists(client_key):
                validator = CertificateValidator(cert_config.cert_dir)
                validation_results = validator.validate_certificate_chain(
                    client_cert,
                    client_key,
                    ca_cert if os.path.exists(ca_cert) else None,
                )

                is_valid, issues = validator.get_validation_summary(validation_results)
                if not is_valid:
                    logger.warning("Certificate validation failed", issues=issues)
                    # Continue anyway for development, but log the issues
                else:
                    logger.info("Certificate validation passed")

                connect_args["sslcert"] = client_cert
                connect_args["sslkey"] = client_key

            if os.path.exists(ca_cert):
                connect_args["sslrootcert"] = ca_cert

        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            pool_timeout=self.settings.pool_timeout,
            pool_recycle=self.settings.pool_recycle,
            echo=False,  # Set to True for SQL debugging
            connect_args=connect_args,
        )

        # Add connection event listeners for logging
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set connection-level settings."""
            logger.debug("Database connection established")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout."""
            logger.debug("Database connection checked out")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin."""
            logger.debug("Database connection checked in")

        self._engine = engine
        self._session_factory = sessionmaker(bind=engine)

        logger.info(
            "Database engine created",
            host=self.settings.host,
            port=self.settings.port,
            database=self.settings.name,
            pool_size=self.settings.pool_size,
        )

        return engine

    def get_session(self) -> Session:
        """Get a database session."""
        if self._session_factory is None:
            self.create_engine()

        return self._session_factory()  # type: ignore[misc]

    def close(self):
        """Close the database engine and all connections."""
        if self._engine is not None:
            self._engine.dispose()
            logger.info("Database engine closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        settings = DatabaseSettings()
        _db_manager = DatabaseManager(settings)
    return _db_manager


def get_session() -> Session:
    """Get a database session."""
    return get_database_manager().get_session()
