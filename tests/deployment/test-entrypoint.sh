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
service docker start || {
    echo "Failed to start Docker service"
    exit 1
}

# Run installation script
echo "Running installation script..."
cd /root && ./install.sh --domain localhost --email test@localhost

# Keep container running
echo "Installation completed. Container is ready for further testing. Use 'docker exec' to run commands."
tail -f /dev/null
