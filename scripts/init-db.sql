-- Initialize the database with extensions and basic setup
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can add some additional ones here

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create user for certificate authentication
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'brownie-fastapi-server') THEN
        CREATE ROLE "brownie-fastapi-server" WITH LOGIN;
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE brownie_metadata TO "brownie-fastapi-server";
GRANT USAGE, CREATE ON SCHEMA public TO "brownie-fastapi-server";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "brownie-fastapi-server";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "brownie-fastapi-server";

-- Grant permissions on future tables (for Alembic migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "brownie-fastapi-server";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "brownie-fastapi-server";

-- Remove password from the initial user after setup
-- This ensures only certificate authentication is used
ALTER USER brownie WITH NOLOGIN;
