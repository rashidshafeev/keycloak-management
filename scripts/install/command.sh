#!/bin/bash

source "./scripts/install/common.sh"

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating kcmanage command..."
        
        # Create command script
        cat > /usr/local/bin/kcmanage << EOL
#!/bin/bash
source "${VENV_DIR}/bin/activate"
python "${INSTALL_DIR}/deploy.py" "\$@"
EOL
        
        # Make command executable
        chmod +x /usr/local/bin/kcmanage || handle_error $? "Failed to make command executable" "create_command"
        
        save_state "command"
    else
        echo "Command already created, skipping..."
    fi
}
