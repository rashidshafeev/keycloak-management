#!/bin/bash
# system_deps.sh - Check and install required system dependencies

# Source common functions
source "$(dirname "$0")/common.sh"

# Function to check if a package is installed
check_package_installed() {
    local package=$1
    if command -v dpkg >/dev/null 2>&1; then
        # Debian/Ubuntu
        if dpkg -l | grep -q "^ii  $package "; then
            return 0
        else
            return 1
        fi
    elif command -v rpm >/dev/null 2>&1; then
        # RHEL/CentOS
        if rpm -q "$package" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        # Unknown package manager, assume not installed
        return 1
    fi
}

# Function to install required packages
install_system_dependencies() {
    echo "Checking system dependencies..."
    
    # Determine OS type
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        echo "Detected Debian/Ubuntu system"
        
        # Required packages
        REQUIRED_PACKAGES=(
            "python3-dev"
            "python3-venv"
            "libssl-dev"
            "libffi-dev"
            "build-essential"
            "curl"
            "jq"
        )
        
        # Check and install packages
        PACKAGES_TO_INSTALL=()
        for pkg in "${REQUIRED_PACKAGES[@]}"; do
            if ! check_package_installed "$pkg"; then
                echo "Package $pkg is not installed, adding to install list"
                PACKAGES_TO_INSTALL+=("$pkg")
            else
                echo "Package $pkg is already installed"
            fi
        done
        
        # Install missing packages
        if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
            echo "Installing missing packages: ${PACKAGES_TO_INSTALL[*]}"
            apt-get update
            apt-get install -y "${PACKAGES_TO_INSTALL[@]}"
        else
            echo "All required packages are already installed"
        fi
        
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        echo "Detected RHEL/CentOS system"
        
        # Required packages
        REQUIRED_PACKAGES=(
            "python3-devel"
            "openssl-devel"
            "libffi-devel"
            "gcc"
            "gcc-c++"
            "make"
            "curl"
            "jq"
        )
        
        # Check and install packages
        PACKAGES_TO_INSTALL=()
        for pkg in "${REQUIRED_PACKAGES[@]}"; do
            if ! check_package_installed "$pkg"; then
                echo "Package $pkg is not installed, adding to install list"
                PACKAGES_TO_INSTALL+=("$pkg")
            else
                echo "Package $pkg is already installed"
            fi
        done
        
        # Install missing packages
        if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
            echo "Installing missing packages: ${PACKAGES_TO_INSTALL[*]}"
            yum install -y "${PACKAGES_TO_INSTALL[@]}"
        else
            echo "All required packages are already installed"
        fi
        
    else
        echo "WARNING: Unsupported system type, cannot install dependencies automatically"
        echo "Please manually install the following dependencies:"
        echo "  - Python 3 development headers"
        echo "  - OpenSSL development libraries"
        echo "  - libffi development libraries"
        echo "  - C compiler and build tools"
        echo "  - curl"
        echo "  - jq"
    fi
    
    # Verify Python and OpenSSL
    echo "Verifying Python and OpenSSL..."
    
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: Python 3 is not installed or not in PATH"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "Python version: $PYTHON_VERSION"
    
    # Check if OpenSSL dev is properly installed by attempting a simple compilation
    echo "Testing OpenSSL development libraries..."
    TEMP_DIR=$(mktemp -d)
    pushd "$TEMP_DIR" >/dev/null || return 1
    
    cat > test_openssl.c << 'EOF'
#include <openssl/ssl.h>
#include <openssl/err.h>

int main() {
    SSL_library_init();
    return 0;
}
EOF
    
    if gcc -o test_openssl test_openssl.c -lssl -lcrypto 2>/dev/null; then
        echo "OpenSSL development libraries are installed correctly"
    else
        echo "WARNING: OpenSSL development libraries may not be correctly installed"
        echo "You may encounter issues with Python cryptography packages"
    fi
    
    popd >/dev/null || return 1
    rm -rf "$TEMP_DIR"
    
    echo "System dependency check complete"
    return 0
}

# This script can be sourced or run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    install_system_dependencies "$@"
fi
