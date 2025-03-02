#!/bin/bash

source "./prepare/common.sh"

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating kcmanage command..."
        
        # Create command script with proper venv activation
        cat > /usr/local/bin/kcmanage << EOL
#!/bin/bash
# Get the directory where Keycloak is installed
INSTALL_DIR="/opt/fawz/keycloak"
VENV_DIR="\${INSTALL_DIR}/venv"

# Activate virtual environment
source "\${VENV_DIR}/bin/activate"
# Export the installation directory so the update command can use it
export INSTALL_DIR
# Execute the Python script with all arguments
python "\${INSTALL_DIR}/kcmanage.py" "\$@"
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

create_command
