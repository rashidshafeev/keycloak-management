#!/bin/bash

# Configuration
INSTALL_DIR="/opt/fawz/keycloak"
VENV_DIR="${INSTALL_DIR}/venv"
LOG_FILE="/var/log/keycloak-install.log"
BACKUP_DIR="/opt/fawz/backup"
STATE_FILE="/opt/fawz/.install_state"

# Initialize state tracking
declare -A completed_steps=()

# Logging setup
setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    echo "Starting test installation at $(date)"
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

# Main installation steps
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "This script must be run as root" 
        exit 1
    fi
}

check_system() {
    # In test environment, we skip interactive prompts
    if ! grep -q 'Ubuntu' /etc/os-release; then
        echo "Warning: Not running on Ubuntu"
    fi

    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [ $total_ram -lt 4096 ]; then
        echo "Warning: Less than 4GB RAM detected"
    fi

    free_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $free_space -lt 20 ]; then
        echo "Warning: Less than 20GB free space detected"
    fi
}

install_dependencies() {
    if [[ -z "${completed_steps[dependencies]}" ]]; then
        echo "Installing dependencies..."
        
        # Update package lists
        apt-get update
        
        # Install system dependencies
        apt-get install -y \
            python3-venv \
            python3-pip \
            python3-dev \
            build-essential \
            libssl-dev \
            libffi-dev \
            git \
            docker.io \
            docker-compose \
            curl \
            wget \
            ufw

        # Start Docker
        service docker start
        
        save_state "dependencies"
    else
        echo "Dependencies already installed, skipping..."
    fi
}

setup_environment() {
    if [[ -z "${completed_steps[environment]}" ]]; then
        echo "Setting up test environment..."
        
        # Create installation directory
        mkdir -p "${INSTALL_DIR}"
        
        # Copy application files
        cp -r /app/* "${INSTALL_DIR}/"
        
        # Copy .env.example to .env
        cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
        
        # Generate test passwords
        KEYCLOAK_ADMIN_PASSWORD="admin_test"
        KEYCLOAK_DB_PASSWORD="keycloak_test"
        GRAFANA_ADMIN_PASSWORD="grafana_test"
        WAZUH_REGISTRATION_PASSWORD="wazuh_test"
        GRAFANA_SMTP_PASSWORD="smtp_test"
        
        # Update the .env file with test values
        sed -i "s/KEYCLOAK_ADMIN_PASSWORD=.*/KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
        sed -i "s/KEYCLOAK_DB_PASSWORD=.*/KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}/" "${INSTALL_DIR}/.env"
        sed -i "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
        sed -i "s/WAZUH_REGISTRATION_PASSWORD=.*/WAZUH_REGISTRATION_PASSWORD=${WAZUH_REGISTRATION_PASSWORD}/" "${INSTALL_DIR}/.env"
        sed -i "s/GRAFANA_SMTP_PASSWORD=.*/GRAFANA_SMTP_PASSWORD=${GRAFANA_SMTP_PASSWORD}/" "${INSTALL_DIR}/.env"
        
        # Update paths for test environment
        sed -i "s#SSL_CERT_PATH=.*#SSL_CERT_PATH=/etc/ssl/certs/test-cert.pem#" "${INSTALL_DIR}/.env"
        sed -i "s#SSL_KEY_PATH=.*#SSL_KEY_PATH=/etc/ssl/private/test-key.pem#" "${INSTALL_DIR}/.env"
        sed -i "s#BACKUP_STORAGE_PATH=.*#BACKUP_STORAGE_PATH=${BACKUP_DIR}#" "${INSTALL_DIR}/.env"
        
        # Update test-specific settings
        sed -i "s/GRAFANA_SMTP_HOST=.*/GRAFANA_SMTP_HOST=localhost/" "${INSTALL_DIR}/.env"
        sed -i "s/GRAFANA_SMTP_USER=.*/GRAFANA_SMTP_USER=test@localhost/" "${INSTALL_DIR}/.env"
        sed -i "s/GRAFANA_SMTP_FROM=.*/GRAFANA_SMTP_FROM=test@localhost/" "${INSTALL_DIR}/.env"
        sed -i "s/GRAFANA_ALERT_EMAIL=.*/GRAFANA_ALERT_EMAIL=admin@localhost/" "${INSTALL_DIR}/.env"
        sed -i "s#GRAFANA_SLACK_WEBHOOK_URL=.*#GRAFANA_SLACK_WEBHOOK_URL=http://localhost:8080/webhook#" "${INSTALL_DIR}/.env"
        sed -i "s/WAZUH_MANAGER_IP=.*/WAZUH_MANAGER_IP=localhost/" "${INSTALL_DIR}/.env"
        sed -i "s/WAZUH_AGENT_NAME=.*/WAZUH_AGENT_NAME=keycloak-test/" "${INSTALL_DIR}/.env"
        
        echo "Test environment file created with test values."
        echo
        echo "Test Credentials:"
        echo "Keycloak Admin: admin/${KEYCLOAK_ADMIN_PASSWORD}"
        echo "Keycloak DB: keycloak/${KEYCLOAK_DB_PASSWORD}"
        echo "Grafana Admin: admin/${GRAFANA_ADMIN_PASSWORD}"
        
        save_state "environment"
    else
        echo "Environment already set up, skipping..."
    fi
}

setup_virtualenv() {
    if [[ -z "${completed_steps[virtualenv]}" ]]; then
        echo "Setting up virtual environment..."
        
        # Create and activate virtual environment
        python3 -m venv "${VENV_DIR}"
        source "${VENV_DIR}/bin/activate"
        
        # Install requirements
        pip install -r "${INSTALL_DIR}/requirements.txt"
        
        save_state "virtualenv"
    else
        echo "Virtual environment already set up, skipping..."
    fi
}

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating keycloak-deploy command..."
        
        cat > /usr/local/bin/keycloak-deploy << EOL
#!/bin/bash
source "${VENV_DIR}/bin/activate"
python "${INSTALL_DIR}/deploy.py" "\$@"
EOL
        
        chmod +x /usr/local/bin/keycloak-deploy
        
        save_state "command"
    else
        echo "Command already created, skipping..."
    fi
}

main() {
    setup_logging
    load_state
    
    check_root
    check_system
    install_dependencies
    setup_environment
    setup_virtualenv
    create_command
    
    echo "Test installation completed successfully!"
}

main "$@"
