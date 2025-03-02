#!/bin/bash

source "./prepare/common.sh"

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating kcmanage command..."
        
        # Create command script with proper venv activation
        cat > /usr/local/bin/kcmanage << EOL
#!/bin/bash
# Get the directory where Keycloak is installed
INSTALL_DIR="\${INSTALL_DIR:-/opt/fawz/keycloak}"
VENV_DIR="\${INSTALL_DIR}/venv"

# Check if virtual environment exists
if [ ! -d "\${VENV_DIR}" ]; then
    echo "Virtual environment not found. Please run the installation script first."
    exit 1
fi

# Activate virtual environment and add package to PYTHONPATH
source "\${VENV_DIR}/bin/activate"
export PYTHONPATH="\${INSTALL_DIR}:\${PYTHONPATH}"

# Execute the Python module with all arguments
python -m kcmanage "\$@"

# Deactivate virtual environment
deactivate
EOL
        
        # Make command executable
        chmod +x /usr/local/bin/kcmanage || handle_error $? "Failed to make command executable" "create_command"
        
        save_state "command"
    else
        echo "Command already created, skipping..."
    fi
}
export -f create_command
