#!/bin/bash

setup_virtualenv() {
    if [[ -z "${completed_steps[virtualenv]}" ]]; then
        echo "Setting up Python environment..."

        # Install Python3 and venv if not present
        if ! command -v python3 &> /dev/null; then
            echo "Installing Python3..."
            apt-get update
            apt-get install -y python3 python3-pip python3-venv build-essential python3-dev
        fi

        # Create virtual environment
        echo "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}" || handle_error $? "Failed to create virtual environment" "setup_virtualenv"

        # Activate virtual environment
        source "${VENV_DIR}/bin/activate" || handle_error $? "Failed to activate virtual environment" "setup_virtualenv"

        # Upgrade pip
        echo "Upgrading pip..."
        pip install --upgrade pip || handle_error $? "Failed to upgrade pip" "setup_virtualenv"

        # Install requirements
        if [ -f "${INSTALL_DIR}/requirements.txt" ]; then
            echo "Installing Python dependencies..."
            pip install -r "${INSTALL_DIR}/requirements.txt" || handle_error $? "Failed to install requirements" "setup_virtualenv"
        else
            handle_error 1 "requirements.txt not found" "setup_virtualenv"
        fi

        # Verify key Python packages are installed
        echo "Verifying Python installation..."
        python3 -c "import click; import docker; import requests" || handle_error $? "Failed to verify Python packages" "setup_virtualenv"

        save_state "virtualenv"
    else
        echo "Virtual environment already set up, skipping..."
    fi
}

export -f setup_virtualenv
