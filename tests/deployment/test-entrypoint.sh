#!/bin/bash

set -x  # Enable debug mode

# Configure passwordless sudo for root
echo "root ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/root

# Wait for Docker to be ready
echo "Waiting for Docker daemon to be ready..."
TIMEOUT=60
COUNTER=0
while ! docker info > /dev/null 2>&1; do
    if [ $COUNTER -ge $TIMEOUT ]; then
        echo "Timeout waiting for Docker daemon"
        echo "Docker daemon log:"
        cat /var/log/dockerd.log
        exit 1
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
done
echo "Docker daemon is ready"

# Set minimal test environment variables
export KEYCLOAK_DOMAIN="localhost"
export ADMIN_EMAIL="test@localhost"
export INSTALL_DIR="/opt/fawz/keycloak"
export REPO_DIR="/app"

# Set git credentials if provided
if [ ! -z "$GIT_USERNAME" ] && [ ! -z "$GIT_PASSWORD" ]; then
    echo "Configuring git credentials..."
    git config --global credential.helper store
    echo "https://${GIT_USERNAME}:${GIT_PASSWORD}@git.rashidshafeev.ru" > ~/.git-credentials
fi

# Configure git
git config --global --add safe.directory "${REPO_DIR}"
git config --global --add safe.directory "${INSTALL_DIR}"

# Initialize git repo in /app if it's not already a repo
if [ ! -d "${REPO_DIR}/.git" ]; then
    cd "${REPO_DIR}"
    git init
    git remote add origin "https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git"
    git fetch
    git checkout -f main
fi

echo "=== Starting Tests ==="

# Test 1: Fresh Installation
echo "Test 1: Fresh installation with domain and email"
cd "${REPO_DIR}"

# Clean up any previous installation
sudo rm -rf "${INSTALL_DIR}"
sudo mkdir -p "${INSTALL_DIR}"

# Copy current repository to install directory
sudo cp -r "${REPO_DIR}/." "${INSTALL_DIR}/"

# Run installation
cd "${INSTALL_DIR}"
sudo ./install.sh --domain "${KEYCLOAK_DOMAIN}" --email "${ADMIN_EMAIL}" --no-clone
if [ $? -ne 0 ]; then
    echo "Test 1 failed: Installation failed"
    echo "Installation log:"
    cat /var/log/keycloak-install.log
    exit 1
fi

# Test 2: Verify Installation
echo "Test 2: Verifying installation"
if ! docker ps | grep -q "keycloak"; then
    echo "Test 2 failed: Keycloak containers not running"
    echo "Docker containers:"
    docker ps -a
    exit 1
fi

# Test 3: Test Reset
echo "Test 3: Testing reset"
cd "${INSTALL_DIR}"
sudo ./install.sh --reset
if [ $? -ne 0 ]; then
    echo "Test 3 failed: Reset failed"
    echo "Installation log:"
    cat /var/log/keycloak-install.log
    exit 1
fi

# Test 4: Verify Reset
echo "Test 4: Verifying reset"
if docker ps | grep -q "keycloak"; then
    echo "Test 4 failed: Keycloak containers still running after reset"
    echo "Docker containers:"
    docker ps -a
    exit 1
fi

if [ -d "${INSTALL_DIR}" ]; then
    echo "Test 4 failed: Installation directory still exists after reset"
    ls -la "${INSTALL_DIR}"
    exit 1
fi

echo "All tests passed!"
exit 0
