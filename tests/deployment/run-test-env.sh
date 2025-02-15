#!/bin/bash

# Build the test container
docker build -t keycloak-test -f Dockerfile.test .

# Run the container with necessary privileges
docker run -d \
    --name keycloak-test-env \
    --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    keycloak-test

echo "Test environment is ready!"
echo "To enter the container: docker exec -it keycloak-test-env bash"
echo "Inside the container, you can run: python3 deploy.py --domain test.local --email test@example.com --config test-config.yaml"
