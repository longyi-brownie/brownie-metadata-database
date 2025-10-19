FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install psycopg2 for alembic compatibility
RUN pip install --no-cache-dir psycopg2-binary

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set default command for migrations
CMD ["alembic", "upgrade", "head"]