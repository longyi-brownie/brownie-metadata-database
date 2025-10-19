"""Database configuration and settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # Database connection
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="brownie_metadata", description="Database name")
    user: str = Field(default="brownie", description="Database user")
    password: str = Field(default="brownie", description="Database password")

    # Connection pool settings
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")

    # Migration settings
    alembic_config: str = Field(
        default="alembic.ini", description="Alembic config file"
    )

    @property
    def database_url(self) -> str:
        """Get the database URL for SQLAlchemy."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    class Config:
        env_prefix = "DB_"
