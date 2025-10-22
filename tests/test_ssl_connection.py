#!/usr/bin/env python3
"""Test SSL connection to PostgreSQL."""

import os
import sys

from sqlalchemy import create_engine

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_ssl_connection():
    """Test SSL connection to PostgreSQL."""
    print("Testing SSL connection to PostgreSQL...")

    # Get database connection details from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "brownie_metadata")
    db_user = os.getenv("DB_USER", "brownie-fastapi-server")
    db_password = os.getenv("DB_PASSWORD", "brownie")

    print(f"Database: {db_user}@{db_host}:{db_port}/{db_name}")

    # Add SSL parameters for certificate authentication
    connect_args = {}
    ssl_mode = os.getenv("DB_SSL_MODE", "verify-full")
    print(f"SSL mode: {ssl_mode}")

    if ssl_mode in ["require", "verify-ca", "verify-full"]:
        connect_args["sslmode"] = ssl_mode

        # Add certificate paths if available
        cert_dir = os.getenv("CERT_DIR", "/certs")
        client_cert = os.path.join(cert_dir, "client.crt")
        client_key = os.path.join(cert_dir, "client.key")
        ca_cert = os.path.join(cert_dir, "ca.crt")

        print(f"Certificate paths - cert_dir: {cert_dir}")
        print(f"client_cert exists: {os.path.exists(client_cert)}")
        print(f"client_key exists: {os.path.exists(client_key)}")
        print(f"ca_cert exists: {os.path.exists(ca_cert)}")

        if os.path.exists(client_cert) and os.path.exists(client_key):
            connect_args["sslcert"] = client_cert
            connect_args["sslkey"] = client_key

        if os.path.exists(ca_cert):
            connect_args["sslrootcert"] = ca_cert

    print(f"Connect args: {connect_args}")

    # Create engine
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Database URL: {database_url}")

    try:
        engine = create_engine(database_url, connect_args=connect_args)
        with engine.connect() as connection:
            from sqlalchemy import text

            result = connection.execute(
                text("SELECT current_user, current_database();")
            )
            row = result.fetchone()
            print(f"✅ Connection successful! User: {row[0]}, Database: {row[1]}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_ssl_connection()
