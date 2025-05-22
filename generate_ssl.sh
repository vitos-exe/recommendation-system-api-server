#!/bin/bash

# Script to generate a self-signed SSL certificate

# Configuration
KEY_FILE="key.pem"
CERT_FILE="cert.pem"
CSR_FILE="server.csr"
DAYS_VALID=365
KEY_BITS=2048
SUBJECT="/C=US/ST=California/L=SanFrancisco/O=MyDevOrg/OU=Development/CN=localhost"

echo "Generating SSL private key ($KEY_FILE)..."
openssl genrsa -out "$KEY_FILE" "$KEY_BITS"
if [ $? -ne 0 ]; then
    echo "Error generating private key."
    exit 1
fi

echo "Generating Certificate Signing Request ($CSR_FILE)..."
openssl req -new -key "$KEY_FILE" -out "$CSR_FILE" -subj "$SUBJECT"
if [ $? -ne 0 ]; then
    echo "Error generating CSR."
    exit 1
fi

echo "Generating self-signed SSL certificate ($CERT_FILE)..."
openssl x509 -req -days "$DAYS_VALID" -in "$CSR_FILE" -signkey "$KEY_FILE" -out "$CERT_FILE"
if [ $? -ne 0 ]; then
    echo "Error generating certificate."
    exit 1
fi

echo "Cleaning up ($CSR_FILE)..."
rm "$CSR_FILE"

echo ""
echo "SSL certificate and private key generated successfully:"
echo "  Private Key: $KEY_FILE"
echo "  Certificate: $CERT_FILE"
echo ""
echo "You can now use these files for your local development server."
echo "Remember to configure your server to use $CERT_FILE and $KEY_FILE."
