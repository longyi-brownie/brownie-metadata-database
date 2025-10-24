FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables to suppress interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NOWARNINGS=yes
ENV PIP_ROOT_USER_ACTION=ignore

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files needed for installation
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -e . --root-user-action=ignore

# Install psycopg2 for alembic compatibility
RUN pip install --no-cache-dir psycopg2-binary --root-user-action=ignore

# Copy application code
COPY . .

# Copy SSL certificates with correct permissions
# Note: These will be overridden by volume mounts in docker-compose.yml for development
# But this ensures the image has certificates with correct permissions
COPY dev-certs/server.crt /var/lib/postgresql/data/server.crt
COPY dev-certs/server.key /var/lib/postgresql/data/server.key
COPY dev-certs/ca.crt /var/lib/postgresql/data/ca.crt

# Set correct ownership and permissions for PostgreSQL certificates
# Following PostgreSQL security guidelines: 600 for private keys, 644 for certificates
# Use user ID 999 (postgres user) and group ID 999
RUN chown 999:999 /var/lib/postgresql/data/server.* && \
    chmod 644 /var/lib/postgresql/data/server.crt && \
    chmod 600 /var/lib/postgresql/data/server.key && \
    chmod 644 /var/lib/postgresql/data/ca.crt

# Create logs directory
RUN mkdir -p /app/logs

# Set default command for migrations
CMD ["alembic", "upgrade", "head"]