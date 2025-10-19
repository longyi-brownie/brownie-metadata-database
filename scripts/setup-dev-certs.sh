#!/bin/bash
# Setup development certificates for PostgreSQL server

set -e

CERT_DIR="dev-certs"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Setting up development certificates for PostgreSQL server..."

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
openssl genrsa -out server.key 4096

# Generate PostgreSQL server certificate signing request
echo "Generating PostgreSQL server certificate signing request..."
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=$DB_HOST"

# Generate PostgreSQL server certificate
echo "Generating PostgreSQL server certificate..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# Clean up CSR files
rm -f *.csr

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo "Development certificates generated successfully!"
echo ""
echo "Certificate files created in $CERT_DIR/:"
echo "  - ca.crt (CA certificate)"
echo "  - server.crt (PostgreSQL server certificate)"
echo "  - server.key (PostgreSQL server private key)"
echo ""
echo "To use these certificates:"
echo "  1. Configure PostgreSQL to use server.crt and server.key"
echo "  2. Set LOCAL_CERT_DIR environment variable to point to this directory"
echo "  3. Client certificates are handled by the FastAPI application"
echo ""
echo "⚠️  WARNING: These are development certificates only!"
echo "   Never use these in production. Use Vault PKI for production certificates."
