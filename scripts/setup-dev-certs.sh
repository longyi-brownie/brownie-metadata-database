#!/bin/bash
# Setup development certificates for local testing

set -e

CERT_DIR="dev-certs"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Setting up development certificates for Brownie Metadata Database..."

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate CA private key
echo "Generating CA private key..."
openssl genrsa -out ca.key 4096

# Generate CA certificate
echo "Generating CA certificate..."
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=Brownie-CA"

# Generate server private key
echo "Generating server private key..."
openssl genrsa -out server.key 4096

# Generate server certificate signing request
echo "Generating server certificate signing request..."
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=$DB_HOST"

# Generate server certificate
echo "Generating server certificate..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# Generate client private key
echo "Generating client private key..."
openssl genrsa -out client.key 4096

# Generate client certificate signing request
echo "Generating client certificate signing request..."
openssl req -new -key client.key -out client.csr -subj "/C=US/ST=CA/L=San Francisco/O=Brownie/OU=Dev/CN=brownie-client"

# Generate client certificate
echo "Generating client certificate..."
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365

# Clean up CSR files
rm -f *.csr

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo "Development certificates generated successfully!"
echo ""
echo "Certificate files created in $CERT_DIR/:"
echo "  - ca.crt (CA certificate)"
echo "  - server.crt (Server certificate)"
echo "  - server.key (Server private key)"
echo "  - client.crt (Client certificate)"
echo "  - client.key (Client private key)"
echo ""
echo "To use these certificates:"
echo "  1. Set LOCAL_CERT_DIR=$CERT_DIR in your environment"
echo "  2. Configure PostgreSQL to use server.crt and server.key"
echo "  3. The application will automatically use client.crt and client.key"
echo ""
echo "⚠️  WARNING: These are development certificates only!"
echo "   Never use these in production. Use Vault for production certificates."
