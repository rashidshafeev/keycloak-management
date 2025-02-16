#!/bin/bash

source "./scripts/install/common.sh"

setup_virtualenv() {
    if [[ -z "${completed_steps[virtualenv]}" ]]; then
        echo "Setting up virtual environment..."
        
        # Create virtual environment
        python3 -m venv "${VENV_DIR}" || handle_error $? "Failed to create virtual environment" "setup_virtualenv"
        
        # Activate virtual environment
        source "${VENV_DIR}/bin/activate" || handle_error $? "Failed to activate virtual environment" "setup_virtualenv"
        
        # Upgrade pip
        pip install --upgrade pip || handle_error $? "Failed to upgrade pip" "setup_virtualenv"
        
        # Install requirements
        if [ -f "${INSTALL_DIR}/requirements.txt" ]; then
            pip install -r "${INSTALL_DIR}/requirements.txt" || handle_error $? "Failed to install requirements" "setup_virtualenv"
        else
            handle_error 1 "requirements.txt not found" "setup_virtualenv"
        fi
        
        save_state "virtualenv"
    else
        echo "Virtual environment already set up, skipping..."
    fi
}
