#!/bin/bash

source "./scripts/install/common.sh"

check_root() {
    if [[ $EUID -ne 0 ]]; then
        handle_error 1 "This script must be run as root" "check_root"
    fi
}

check_system() {
    echo "Checking system requirements..."
    
    # Get OS information
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        OS=$(uname -s)
    fi
    
    case "$OS" in
        "Ubuntu"|"Alpine Linux")
            echo "Running on supported system: $OS"
            ;;
        *)
            echo "Warning: This script is primarily tested on Ubuntu and Alpine Linux. Other distributions may not work correctly."
            ;;
    esac
    
    # Check for required commands
    local required_commands=(
        "git"
        "python3"
        "docker"
    )
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            handle_error 1 "Required command '$cmd' not found" "check_system"
        fi
    done
}
