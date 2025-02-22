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

# We don't need to start Docker daemon when running in Docker

# Copy install script to home directory (simulating real user scenario)
echo "Copying install script to home directory..."
cp /root/install.sh /root/
cd /root

# Make script executable
chmod +x install.sh

# Run installation script
echo "Running installation script..."
./install.sh

# Keep container running
echo "Installation completed. Container is ready for further testing. Use 'docker exec' to run commands."
tail -f /dev/null
