#!/bin/bash

# Exit on error
set -e

echo "Setting up test environment..."

# Start Keycloak and PostgreSQL
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
timeout=300
while [ $timeout -gt 0 ]; do
    if docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        echo "Services are ready!"
        break
    fi
    echo "Waiting for services... ($timeout seconds remaining)"
    sleep 5
    timeout=$((timeout - 5))
done

if [ $timeout -eq 0 ]; then
    echo "Timeout waiting for services"
    exit 1
fi

# Create test data directory if it doesn't exist
mkdir -p tests/data/{realms,clients,users}

# Copy test configurations
cp tests/config/test_config.yml tests/data/

echo "Test environment is ready!"
