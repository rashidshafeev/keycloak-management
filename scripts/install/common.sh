#!/bin/bash

# Essential paths
INSTALL_DIR="${INSTALL_DIR:-/opt/fawz/keycloak}"
VENV_DIR="${VENV_DIR:-${INSTALL_DIR}/venv}"
LOG_FILE="${LOG_FILE:-/var/log/keycloak-install.log}"
STATE_FILE="${STATE_FILE:-/opt/fawz/.install_state}"

# Repository settings
REPO_URL="${REPO_URL:-https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git}"

# Initialize state tracking
declare -A completed_steps

# Logging setup
setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    echo "Starting installation at $(date)"
}

# State management
save_state() {
    local step=$1
    completed_steps[$step]=1
    mkdir -p "$(dirname "$STATE_FILE")"
    printf "%s\n" "${!completed_steps[@]}" > "$STATE_FILE"
}

load_state() {
    if [[ -f "$STATE_FILE" ]]; then
        while IFS= read -r step; do
            completed_steps[$step]=1
        done < "$STATE_FILE"
    fi
}

# Error handling
handle_error() {
    local exit_code=$1
    local error_msg=$2
    local step_name=$3
    
    echo "Error in step ${step_name}: ${error_msg}"
    echo "Exit code: ${exit_code}"
    
    # Log error details
    {
        echo "=== Error Details ==="
        echo "Timestamp: $(date)"
        echo "Step: ${step_name}"
        echo "Error Message: ${error_msg}"
        echo "Exit Code: ${exit_code}"
        echo "===================="
    } >> "$LOG_FILE"
    
    exit "${exit_code}"
}

clone_repository() {
    if [[ -z "${completed_steps[repository]}" ]]; then
        echo "Setting up repository..."
        
        # Configure git to trust this directory if needed
        if ! git config --global --get-all safe.directory | grep -q "^${INSTALL_DIR}\$"; then
            echo "Configuring git to trust ${INSTALL_DIR}..."
            git config --global --add safe.directory "${INSTALL_DIR}"
        fi
        
        # Update repository if it exists
        if [ -d "${INSTALL_DIR}/.git" ]; then
            echo "Repository exists, updating..."
            cd "${INSTALL_DIR}"
            git pull
        fi
        
        save_state "repository"
    else
        echo "Repository already set up, skipping..."
    fi
}

reset_installation() {
    echo "Performing reset..."
    
    # Stop and remove Docker containers
    if [ -f "${INSTALL_DIR}/docker-compose.yml" ]; then
        echo "Stopping Docker containers..."
        cd "${INSTALL_DIR}" && docker-compose down -v || true
    fi
    
    # Stop all containers with 'keycloak' in their name
    echo "Stopping any remaining Keycloak containers..."
    docker ps -aq --filter "name=keycloak" | xargs -r docker rm -f || true
    docker ps -aq --filter "name=postgres" | xargs -r docker rm -f || true
    
    # Remove all volumes
    echo "Removing Docker volumes..."
    docker volume ls -q --filter "name=keycloak" | xargs -r docker volume rm || true
    
    # Clean up Docker system
    echo "Cleaning up Docker system..."
    docker system prune -f || true

    # Remove all directories and files
    echo "Removing installation files..."
    rm -rf "${INSTALL_DIR}" 2>/dev/null || true
    rm -f /usr/local/bin/kcmanage 2>/dev/null || true
    rm -f "${STATE_FILE}" 2>/dev/null || true

    # Reset state
    completed_steps=()
    
    echo "Reset completed successfully."
}

# Export functions and variables
export -f handle_error
export -f save_state
export -f load_state
export -f clone_repository
export -f reset_installation
export -f setup_logging
export completed_steps
export INSTALL_DIR
export VENV_DIR
export LOG_FILE
export STATE_FILE
export REPO_URL
