#!/bin/bash
# Setup development certificates for FastAPI server to connect to PostgreSQL

set -e

CERT_DIR="fastapi-certs"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Setting up development certificates for FastAPI server → PostgreSQL..."

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate CA private key
echo "Generating CA private key..."
openssl genrsa -out ca.key 4096

# Generate CA certificate
echo "Generating CA certificate..."
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=Brownie-CA"

# Generate PostgreSQL server private key
echo "Generating PostgreSQL server private key..."
openssl genrsa -out postgres-server.key 4096

# Generate PostgreSQL server certificate signing request
echo "Generating PostgreSQL server certificate signing request..."
openssl req -new -key postgres-server.key -out postgres-server.csr -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=$DB_HOST"

# Generate PostgreSQL server certificate
echo "Generating PostgreSQL server certificate..."
openssl x509 -req -in postgres-server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out postgres-server.crt -days 365

# Generate FastAPI client private key
echo "Generating FastAPI client private key..."
openssl genrsa -out fastapi-client.key 4096

# Generate FastAPI client certificate signing request
echo "Generating FastAPI client certificate signing request..."
openssl req -new -key fastapi-client.key -out fastapi-client.csr -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=brownie-fastapi-server"

# Generate FastAPI client certificate
echo "Generating FastAPI client certificate..."
openssl x509 -req -in fastapi-client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out fastapi-client.crt -days 365

# Clean up CSR files
rm -f *.csr

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo "Development certificates generated successfully!"
echo ""
echo "Certificate files created in $CERT_DIR/:"
echo "  - ca.crt (CA certificate)"
echo "  - postgres-server.crt (PostgreSQL server certificate)"
echo "  - postgres-server.key (PostgreSQL server private key)"
echo "  - fastapi-client.crt (FastAPI client certificate)"
echo "  - fastapi-client.key (FastAPI client private key)"
echo ""
echo "To use these certificates:"
echo "  1. Copy fastapi-client.* to your FastAPI server project"
echo "  2. Configure PostgreSQL to use postgres-server.crt and postgres-server.key"
echo "  3. FastAPI server will automatically read certificates from /certs directory"
echo ""
echo "⚠️  WARNING: These are development certificates only!"
echo "   Never use these in production. Use Vault PKI for production certificates."
