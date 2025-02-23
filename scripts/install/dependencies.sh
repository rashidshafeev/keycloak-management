#!/bin/bash

source "${SCRIPTS_DIR}/common.sh"

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
            "Ubuntu")
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
                    docker.io \
                    docker-compose \
                    curl \
                    wget \
                    ufw || handle_error $? "Failed to install packages" "install_dependencies"
                
                # Start and enable Docker
                systemctl start docker || handle_error $? "Failed to start Docker" "install_dependencies"
                systemctl enable docker || handle_error $? "Failed to enable Docker" "install_dependencies"

                # Add current user to docker group if not root
                if [[ $EUID -ne 0 ]]; then
                    usermod -aG docker $USER || handle_error $? "Failed to add user to docker group" "install_dependencies"
                fi
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
