#!/bin/bash

source "${SCRIPTS_DIR}/common.sh"

install_docker() {
    echo "Installing Docker using official method..."
    
    # First, uninstall any conflicting packages
    echo "Removing old Docker packages if they exist..."
    for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
        apt-get remove -y $pkg || true
    done

    # Add Docker's official GPG key
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources
    # Handle derivative distributions by using debian as the base
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
        bookworm stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Update apt and install Docker
    apt-get update
    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    # Start and enable Docker
    if command -v systemctl &> /dev/null; then
        systemctl start docker || true
        systemctl enable docker || true
    fi

    # Create docker group and add current user if not root
    if [[ $EUID -ne 0 ]]; then
        groupadd docker || true
        usermod -aG docker $USER || true
    fi

    # Verify Docker installation
    if ! docker run --rm hello-world &> /dev/null; then
        echo "Warning: Docker installation verification failed. Please check Docker installation manually."
    fi

    # Configure UFW to work with Docker if UFW is installed
    if command -v ufw &> /dev/null; then
        echo "Configuring UFW for Docker..."
        # Create UFW Docker rules file
        cat > /etc/ufw/applications.d/docker <<EOF
[Docker]
title=Docker
description=Docker container engine
ports=2375,2376,2377,7946/tcp|7946/udp|4789/udp
EOF
        ufw reload
        # Add rules to the DOCKER-USER chain
        iptables -N DOCKER-USER || true
        iptables -A DOCKER-USER -j RETURN
    fi
}

install_dependencies() {
    if [[ -z "${completed_steps[dependencies]}" ]]; then
        echo "Installing dependencies..."
        
        # Get OS information
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
        else
            OS=$(uname -s)
        fi
        
        # First, try to install Python regardless of OS
        if ! command -v python3 &> /dev/null; then
            echo "Python3 not found. Installing..."
            apt-get update
            apt-get install -y python3 python3-pip python3-venv
        fi
        
        case "$OS" in
            "Ubuntu"|"Debian GNU/Linux")
                # Update package lists
                apt-get update || handle_error $? "Failed to update package lists" "install_dependencies"
                
                # Install system dependencies
                apt-get install -y \
                    python3-venv \
                    python3-pip \
                    python3-dev \
                    build-essential \
                    libssl-dev \
                    libffi-dev \
                    git \
                    curl \
                    wget \
                    ufw || handle_error $? "Failed to install packages" "install_dependencies"
                
                # Install Docker using official method
                install_docker
                ;;
            "Alpine Linux")
                # Alpine dependencies
                apk add --no-cache \
                    python3 \
                    py3-pip \
                    python3-dev \
                    gcc \
                    musl-dev \
                    openssl-dev \
                    libffi-dev \
                    git \
                    docker \
                    docker-compose \
                    curl \
                    wget || handle_error $? "Failed to install packages" "install_dependencies"
                ;;
            *)
                # For unsupported systems, try to install Python using apt-get
                if [ -x "$(command -v apt-get)" ]; then
                    echo "Debian-based system detected. Installing dependencies..."
                    apt-get update
                    apt-get install -y \
                        python3 \
                        python3-pip \
                        python3-venv \
                        git \
                        curl

                    # Install Docker using official method
                    install_docker
                else
                    echo "Warning: Unsupported system. Please install dependencies manually:"
                    echo "- Python 3"
                    echo "- pip"
                    echo "- Docker"
                    echo "- Docker Compose"
                    echo "- Git"
                fi
                ;;
        esac
        
        save_state "dependencies"
    else
        echo "Dependencies already installed, skipping..."
    fi
}
