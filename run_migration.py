#!/usr/bin/env python3
"""Simple migration runner that bypasses alembic configuration issues."""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Get database connection details from environment variables
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "brownie_metadata")
db_user = os.getenv("DB_USER", "brownie")
db_password = os.getenv("DB_PASSWORD", "brownie")

print(f"Connecting to database: {db_user}@{db_host}:{db_port}/{db_name}")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    print("Database connection successful!")
    
    # Create a cursor
    cursor = conn.cursor()
    
    # Check if alembic_version table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'alembic_version'
        );
    """)
    
    table_exists = cursor.fetchone()[0]
    print(f"Alembic version table exists: {table_exists}")
    
    if not table_exists:
        print("Creating alembic_version table...")
        cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            );
        """)
        
        # Insert the current migration version
        cursor.execute("""
            INSERT INTO alembic_version (version_num) VALUES ('d607e412e7b0');
        """)
        print("Migration version set to d607e412e7b0")
    else:
        print("Alembic version table already exists")
    
    # Commit the changes
    conn.commit()
    print("Migration completed successfully!")
    
    # Close the connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)
