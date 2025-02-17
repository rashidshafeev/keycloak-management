#!/bin/bash

# Clean up any existing test environment
docker-compose -f docker-compose.test.yml down -v

# Build and start the test environment
docker-compose -f docker-compose.test.yml up --build -d

echo "Test environment is starting..."
echo "Waiting for services to be ready..."
sleep 10

# Check if containers are running
if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
    echo "Error: Containers failed to start. Checking logs..."
    docker-compose -f docker-compose.test.yml logs
    exit 1
fi

echo "Test environment is ready!"
echo "Available commands:"
echo "- View logs: docker-compose -f docker-compose.test.yml logs -f"
echo "- Enter container: docker-compose -f docker-compose.test.yml exec keycloak-test bash"
echo "- Stop environment: docker-compose -f docker-compose.test.yml down"
