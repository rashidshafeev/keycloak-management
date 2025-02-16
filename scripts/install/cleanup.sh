#!/bin/bash

source "./scripts/install/common.sh"

cleanup_repository() {
    echo "Cleaning up repository..."
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
    fi
}

cleanup_command() {
    echo "Cleaning up keycloak-deploy command..."
    if [[ -f "/usr/local/bin/keycloak-deploy" ]]; then
        rm -f "/usr/local/bin/keycloak-deploy"
    fi
}

backup_existing() {
    if [[ -d "$INSTALL_DIR" ]]; then
        echo "Backing up existing installation..."
        local backup_dir="/opt/fawz/backup"
        local backup_name="keycloak_backup_$(date +%Y%m%d_%H%M%S)"
        local backup_path="$backup_dir/$backup_name"
        
        mkdir -p "$backup_dir"
        cp -r "$INSTALL_DIR" "$backup_path"
        echo "Backup created at $backup_path"
    fi
}

reset_installation() {
    # Backup before reset
    backup_existing
    
    # Stop and remove Docker containers
    if command -v docker &> /dev/null; then
        echo "Stopping Docker containers..."
        docker-compose down -v || true
    fi
    
    # Clean up repository
    cleanup_repository
    
    # Clean up command
    cleanup_command
    
    # Clean up virtualenv
    if [[ -d "$VENV_DIR" ]]; then
        echo "Cleaning up virtualenv..."
        rm -rf "$VENV_DIR"
    fi
    
    # Clean up state file
    if [[ -f "$STATE_FILE" ]]; then
        echo "Cleaning up state file..."
        rm -f "$STATE_FILE"
    fi
    
    return 0
}
