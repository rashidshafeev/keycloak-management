#!/bin/bash

# Essential paths
INSTALL_DIR="${INSTALL_DIR:-/opt/fawz/keycloak}"
VENV_DIR="${VENV_DIR:-${INSTALL_DIR}/venv}"
STATE_FILE="${STATE_FILE:-${INSTALL_DIR}/.install_state}"

# Initialize state tracking
declare -A completed_steps

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
    exit "${exit_code}"
}

# Export functions and variables
export -f handle_error
export -f save_state
export -f load_state
export completed_steps
export INSTALL_DIR
export VENV_DIR
export STATE_FILE
