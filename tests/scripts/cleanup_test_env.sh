#!/bin/bash

# Exit on error
set -e

echo "Cleaning up test environment..."

# Stop and remove containers
docker-compose -f docker-compose.test.yml down -v

# Remove test data
rm -rf tests/data/*

echo "Test environment cleaned up!"
