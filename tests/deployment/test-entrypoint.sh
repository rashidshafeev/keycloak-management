#!/bin/bash

set -x  # Enable debug mode

# Configure passwordless sudo for root
echo "root ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/root

# Configure Git credentials if provided
if [ ! -z "$GIT_USERNAME" ] && [ ! -z "$GIT_PASSWORD" ]; then
    echo "Configuring Git credentials..."
    git config --global credential.helper store
    echo "https://${GIT_USERNAME}:${GIT_PASSWORD}@git.rashidshafeev.ru" > ~/.git-credentials
    chmod 600 ~/.git-credentials
fi

# Start Docker daemon
if command -v systemctl >/dev/null 2>&1; then
    systemctl start docker
else
    service docker start || {
        echo "Failed to start Docker service"
        exit 1
    }
fi

# Wait for Docker to be ready
echo "Waiting for Docker daemon to be ready..."
TIMEOUT=60
COUNTER=0
while ! docker info > /dev/null 2>&1; do
    if [ $COUNTER -ge $TIMEOUT ]; then
        echo "Timeout waiting for Docker daemon"
        echo "Docker daemon status:"
        if command -v systemctl >/dev/null 2>&1; then
            systemctl status docker
            journalctl -xe
        else
            service docker status
        fi
        exit 1
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
done
echo "Docker daemon is ready"

echo "=== Starting Tests ==="

# Test 1: Clone the repository (simulating git clone on VPS)
echo "Test 1: Cloning repository to /opt/fawz/keycloak"
mkdir -p /opt/fawz/keycloak
git clone https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git /opt/fawz/keycloak
if [ $? -ne 0 ]; then
    echo "Test 1 failed: Repository clone failed"
    exit 1
fi

# Test 2: Run installation
echo "Test 2: Running fresh installation"
cd /opt/fawz/keycloak
./install.sh --domain localhost --email test@localhost --no-clone
if [ $? -ne 0 ]; then
    echo "Test 2 failed: Installation failed"
    echo "Installation log:"
    cat /var/log/keycloak-install.log
    exit 1
fi

# Test 3: Verify Installation
echo "Test 3: Verifying services are running"
sleep 10  # Give services time to start

# Check if Keycloak containers are running
if ! docker ps | grep -q "keycloak"; then
    echo "Test 3 failed: Keycloak containers not running"
    echo "Docker containers:"
    docker ps -a
    exit 1
fi

# Test 4: Check keycloak-deploy command
echo "Test 4: Testing keycloak-deploy command"
if ! command -v keycloak-deploy &> /dev/null; then
    echo "Test 4 failed: keycloak-deploy command not found"
    exit 1
fi

# Test 5: Test Reset
echo "Test 5: Testing reset functionality"
./install.sh --reset
if [ $? -ne 0 ]; then
    echo "Test 5 failed: Reset failed"
    echo "Installation log:"
    cat /var/log/keycloak-install.log
    exit 1
fi

# Verify reset was successful
if docker ps | grep -q "keycloak"; then
    echo "Test 5 failed: Keycloak containers still running after reset"
    echo "Docker containers:"
    docker ps -a
    exit 1
fi

if [ -d "/opt/fawz/keycloak" ]; then
    echo "Test 5 failed: Installation directory still exists after reset"
    ls -la "/opt/fawz/keycloak"
    exit 1
fi

echo "All tests passed!"
exit 0
