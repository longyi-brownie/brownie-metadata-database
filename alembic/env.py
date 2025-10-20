import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, engine_from_config, pool

from alembic import context

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import our models
from database.base import Base
from database.models import *  # Import all models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    print("DEBUG: Starting run_migrations_online")

    # Override the database URL with environment variables if available
    configuration = config.get_section(config.config_ini_section, {})
    print(f"DEBUG: Original configuration: {configuration}")

    # Get database connection details from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "brownie_metadata")
    db_user = os.getenv("DB_USER", "brownie-fastapi-server")
    db_password = os.getenv("DB_PASSWORD", "")
    db_ssl_mode = os.getenv("DB_SSL_MODE", "prefer")

    print(
        f"DEBUG: Environment variables - DB_HOST: {db_host}, DB_PORT: {db_port}, DB_NAME: {db_name}, DB_USER: {db_user}, DB_SSL_MODE: {db_ssl_mode}"
    )

    # Construct the database URL (SSL mode will be handled in connect_args)
    if db_password:
        database_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
    else:
        database_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    print(f"DEBUG: Using database URL: {database_url}")
    configuration["sqlalchemy.url"] = database_url
    print(f"DEBUG: Updated configuration: {configuration}")

    # Add SSL parameters for certificate authentication
    connect_args = {}
    ssl_mode = os.getenv("DB_SSL_MODE", "require")
    print(f"DEBUG: SSL mode: {ssl_mode}")

    if ssl_mode in ["require", "verify-ca", "verify-full"]:
        connect_args["sslmode"] = ssl_mode

        # Add certificate paths if available
        cert_dir = os.getenv("CERT_DIR", "/certs")
        client_cert = os.path.join(cert_dir, "client.crt")
        client_key = os.path.join(cert_dir, "client.key")
        ca_cert = os.path.join(cert_dir, "ca.crt")

        print(f"DEBUG: Certificate paths - cert_dir: {cert_dir}")
        print(f"DEBUG: client_cert exists: {os.path.exists(client_cert)}")
        print(f"DEBUG: client_key exists: {os.path.exists(client_key)}")
        print(f"DEBUG: ca_cert exists: {os.path.exists(ca_cert)}")

        if os.path.exists(client_cert) and os.path.exists(client_key):
            connect_args["sslcert"] = client_cert
            connect_args["sslkey"] = client_key

        if os.path.exists(ca_cert):
            connect_args["sslrootcert"] = ca_cert

    print(f"DEBUG: Connect args: {connect_args}")

    # Create engine directly with SSL parameters
    database_url = configuration["sqlalchemy.url"]
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Let alembic handle the execution timing
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
