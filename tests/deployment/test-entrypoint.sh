#!/bin/bash

# Start Docker daemon
service docker start

# Wait for Docker to be ready
while ! docker info > /dev/null 2>&1; do
    echo "Waiting for Docker to start..."
    sleep 1
done

# Keep container running
tail -f /dev/null
