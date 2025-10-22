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

# Generate PostgreSQL server certificate signing request with SAN
echo "Generating PostgreSQL server certificate signing request..."
cat > server.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = Brownie
OU = Dev
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = postgres
IP.1 = 127.0.0.1
EOF

openssl req -new -key server.key -out server.csr -config server.conf

# Generate PostgreSQL server certificate
echo "Generating PostgreSQL server certificate..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -extensions v3_req -extfile server.conf

# Generate client certificate for FastAPI with proper EKU
echo "Generating client certificate for FastAPI..."
openssl genrsa -out client.key 4096

# Create client certificate config with Extended Key Usage
cat > client.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = Brownie
OU = Dev
CN = brownie-fastapi-server

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

openssl req -new -key client.key -out client.csr -config client.conf
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -extensions v3_req -extfile client.conf

# Clean up CSR and config files
rm -f *.csr server.conf client.conf

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo "Development certificates generated successfully!"
echo ""
echo "Certificate files created in $CERT_DIR/:"
echo "  - ca.crt (CA certificate)"
echo "  - server.crt (PostgreSQL server certificate)"
echo "  - server.key (PostgreSQL server private key)"
echo "  - client.crt (FastAPI client certificate)"
echo "  - client.key (FastAPI client private key)"
echo ""
echo "To use these certificates:"
echo "  1. Configure PostgreSQL to use server.crt and server.key"
echo "  2. Set LOCAL_CERT_DIR environment variable to point to this directory"
echo "  3. Client certificates are handled by the FastAPI application"
echo ""
echo "⚠️  WARNING: These are development certificates only!"
echo "   Never use these in production. Use Vault PKI for production certificates."
