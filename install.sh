#!/bin/bash

# Configuration
REPO_URL="https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git"
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

# Cleanup functions
cleanup_repository() {
    echo "Cleaning up repository..."
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
    fi
}

cleanup_venv() {
    echo "Cleaning up virtual environment..."
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
    fi
}

cleanup_command() {
    echo "Removing deployed command..."
    if [[ -f "/usr/local/bin/keycloak-deploy" ]]; then
        rm -f "/usr/local/bin/keycloak-deploy"
    fi
}

backup_existing() {
    if [[ -d "$INSTALL_DIR" ]]; then
        echo "Backing up existing installation..."
        mkdir -p "$BACKUP_DIR"
        local backup_name="keycloak_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$INSTALL_DIR" "$BACKUP_DIR/$backup_name"
        echo "Backup created at $BACKUP_DIR/$backup_name"
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
    # Check OS
    if ! grep -q 'Ubuntu' /etc/os-release; then
        echo "This script is designed for Ubuntu. Other distributions may not work correctly."
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check minimum RAM (4GB)
    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [ $total_ram -lt 4096 ]; then
        echo "Warning: Less than 4GB RAM detected. This may impact performance."
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check disk space (20GB minimum)
    free_space=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $free_space -lt 20 ]; then
        echo "Warning: Less than 20GB free space detected. This may be insufficient."
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

install_dependencies() {
    if [[ -z "${completed_steps[dependencies]}" ]]; then
        echo "Installing dependencies..."
        apt-get update
        apt-get install -y \
            python3-venv \
            python3-pip \
            git \
            docker.io \
            docker-compose \
            curl \
            wget \
            ufw

        # Start and enable Docker
        systemctl start docker
        systemctl enable docker

        # Add current user to docker group if not root
        if [[ $EUID -ne 0 ]]; then
            usermod -aG docker $USER
        fi

        save_state "dependencies"
    else
        echo "Dependencies already installed, skipping..."
    fi
}

clone_repository() {
    if [[ -z "${completed_steps[repository]}" ]]; then
        echo "Setting up repository..."
        mkdir -p "$INSTALL_DIR"
        cd "$INSTALL_DIR"
        
        if [ ! -d "${INSTALL_DIR}/.git" ]; then
            git clone "$REPO_URL" .
        else
            git pull
        fi
        save_state "repository"
    else
        echo "Repository already set up, skipping..."
    fi
}

setup_environment() {
    if [[ -z "${completed_steps[environment]}" ]]; then
        echo "Setting up environment..."
        
        # Copy example environment file if not exists
        if [ ! -f "${INSTALL_DIR}/.env" ]; then
            if [ ! -f "${INSTALL_DIR}/.env.example" ]; then
                echo "Error: .env.example not found!"
                exit 1
            fi
            
            cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
            
            # Generate secure passwords
            KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -base64 12)
            KEYCLOAK_DB_PASSWORD=$(openssl rand -base64 12)
            GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 12)
            WAZUH_REGISTRATION_PASSWORD=$(openssl rand -base64 12)
            GRAFANA_SMTP_PASSWORD=$(openssl rand -base64 12)
            
            # Get system hostname for domain suggestion
            HOSTNAME=$(hostname -f)
            
            # Update Keycloak settings
            sed -i "s/KEYCLOAK_ADMIN=.*/KEYCLOAK_ADMIN=admin/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_ADMIN_PASSWORD=.*/KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_DB_PASSWORD=.*/KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}/" "${INSTALL_DIR}/.env"
            
            # Update Docker settings
            sed -i "s/DOCKER_REGISTRY=.*/DOCKER_REGISTRY=docker.io/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_VERSION=.*/KEYCLOAK_VERSION=latest/" "${INSTALL_DIR}/.env"
            sed -i "s/POSTGRES_VERSION=.*/POSTGRES_VERSION=latest/" "${INSTALL_DIR}/.env"
            
            # Update SSL settings (will be prompted during deployment)
            sed -i "s#SSL_CERT_PATH=.*#SSL_CERT_PATH=/etc/letsencrypt/live/${HOSTNAME}/fullchain.pem#" "${INSTALL_DIR}/.env"
            sed -i "s#SSL_KEY_PATH=.*#SSL_KEY_PATH=/etc/letsencrypt/live/${HOSTNAME}/privkey.pem#" "${INSTALL_DIR}/.env"
            
            # Update Prometheus settings
            sed -i "s/PROMETHEUS_SCRAPE_INTERVAL=.*/PROMETHEUS_SCRAPE_INTERVAL=15s/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_EVAL_INTERVAL=.*/PROMETHEUS_EVAL_INTERVAL=15s/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_RETENTION_TIME=.*/PROMETHEUS_RETENTION_TIME=15d/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_STORAGE_SIZE=.*/PROMETHEUS_STORAGE_SIZE=50GB/" "${INSTALL_DIR}/.env"
            
            # Update Grafana settings
            sed -i "s/GRAFANA_ADMIN_USER=.*/GRAFANA_ADMIN_USER=admin/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
            
            # Update Grafana SMTP settings (will be prompted during deployment)
            sed -i "s/GRAFANA_SMTP_ENABLED=.*/GRAFANA_SMTP_ENABLED=true/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_HOST=.*/GRAFANA_SMTP_HOST=smtp.example.com/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_PORT=.*/GRAFANA_SMTP_PORT=587/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_USER=.*/GRAFANA_SMTP_USER=alerts@example.com/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_PASSWORD=.*/GRAFANA_SMTP_PASSWORD=${GRAFANA_SMTP_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_FROM=.*/GRAFANA_SMTP_FROM=alerts@example.com/" "${INSTALL_DIR}/.env"
            
            # Update Grafana alert settings
            sed -i "s/GRAFANA_ALERT_EMAIL=.*/GRAFANA_ALERT_EMAIL=admin@example.com/" "${INSTALL_DIR}/.env"
            sed -i "s#GRAFANA_SLACK_WEBHOOK_URL=.*#GRAFANA_SLACK_WEBHOOK_URL=#" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SLACK_CHANNEL=.*/GRAFANA_SLACK_CHANNEL=#alerts/" "${INSTALL_DIR}/.env"
            
            # Update Wazuh settings
            sed -i "s/WAZUH_MANAGER_IP=.*/WAZUH_MANAGER_IP=localhost/" "${INSTALL_DIR}/.env"
            sed -i "s/WAZUH_REGISTRATION_PASSWORD=.*/WAZUH_REGISTRATION_PASSWORD=${WAZUH_REGISTRATION_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/WAZUH_AGENT_NAME=.*/WAZUH_AGENT_NAME=keycloak-${HOSTNAME}/" "${INSTALL_DIR}/.env"
            
            # Update Firewall settings
            sed -i "s/FIREWALL_MAX_BACKUPS=.*/FIREWALL_MAX_BACKUPS=5/" "${INSTALL_DIR}/.env"
            sed -i "s/FIREWALL_ALLOWED_PORTS=.*/FIREWALL_ALLOWED_PORTS=22,80,443,8080,8443,3000,9090,9100,9323/" "${INSTALL_DIR}/.env"
            sed -i "s/FIREWALL_ADMIN_IPS=.*/FIREWALL_ADMIN_IPS=127.0.0.1/" "${INSTALL_DIR}/.env"
            
            # Update Backup settings
            sed -i "s#BACKUP_STORAGE_PATH=.*#BACKUP_STORAGE_PATH=/opt/fawz/backup#" "${INSTALL_DIR}/.env"
            sed -i "s/BACKUP_RETENTION_DAYS=.*/BACKUP_RETENTION_DAYS=30/" "${INSTALL_DIR}/.env"
            
            # Update Logging settings
            sed -i "s/LOG_LEVEL=.*/LOG_LEVEL=INFO/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_FORMAT=.*/LOG_FORMAT=json/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_MAX_SIZE=.*/LOG_MAX_SIZE=100MB/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_MAX_FILES=.*/LOG_MAX_FILES=10/" "${INSTALL_DIR}/.env"
            
            echo "Environment file created with secure defaults."
            echo
            echo "IMPORTANT: Your generated passwords are:"
            echo "Keycloak Admin Password: ${KEYCLOAK_ADMIN_PASSWORD}"
            echo "Keycloak DB Password: ${KEYCLOAK_DB_PASSWORD}"
            echo "Grafana Admin Password: ${GRAFANA_ADMIN_PASSWORD}"
            echo "Wazuh Registration Password: ${WAZUH_REGISTRATION_PASSWORD}"
            echo "Please save these passwords in a secure location!"
            echo
            echo "The following settings will need to be configured during deployment:"
            echo "1. SSL certificate paths (if using HTTPS)"
            echo "2. SMTP settings (if using email alerts)"
            echo "3. Slack webhook URL (if using Slack notifications)"
            echo "4. Firewall admin IPs"
            echo
            echo "Review and modify the environment file if needed:"
            echo "nano ${INSTALL_DIR}/.env"
            
            # Ask user if they want to edit the file
            read -p "Would you like to edit the environment file now? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-nano} "${INSTALL_DIR}/.env"
            fi
        else
            echo "Environment file already exists, skipping..."
        fi
        
        save_state "environment"
    else
        echo "Environment already configured, skipping..."
    fi
}

setup_virtualenv() {
    if [[ -z "${completed_steps[virtualenv]}" ]]; then
        echo "Setting up virtual environment..."
        cd "$INSTALL_DIR"
        python3 -m venv "$VENV_DIR"
        source "${VENV_DIR}/bin/activate"
        pip install --upgrade pip
        pip install -r requirements.txt
        save_state "virtualenv"
    else
        echo "Virtual environment already set up, skipping..."
    fi
}

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating keycloak-deploy command..."
        cat > /usr/local/bin/keycloak-deploy << 'EOL'
#!/bin/bash
source /opt/fawz/keycloak/venv/bin/activate
cd /opt/fawz/keycloak
exec python deploy.py "$@"
EOL
        chmod +x /usr/local/bin/keycloak-deploy
        save_state "command"
    else
        echo "Command already created, skipping..."
    fi
}

# Error handling
handle_error() {
    local exit_code=$?
    local failed_step=$1
    
    echo "Error occurred during $failed_step (exit code: $exit_code)"
    
    case $failed_step in
        "dependencies")
            # No specific cleanup needed for dependencies
            ;;
        "repository")
            cleanup_repository
            ;;
        "environment")
            cleanup_repository
            ;;
        "virtualenv")
            cleanup_venv
            cleanup_repository
            ;;
        "command")
            cleanup_command
            cleanup_venv
            cleanup_repository
            ;;
    esac
    
    if [[ -f "$STATE_FILE" ]]; then
        rm -f "$STATE_FILE"
    fi
    
    echo "Cleanup completed. Check $LOG_FILE for details."
    exit $exit_code
}

# Main execution
main() {
    setup_logging
    check_root
    check_system
    load_state
    
    # Backup existing installation
    backup_existing
    
    # Installation steps with error handling
    trap 'handle_error "dependencies"' ERR
    install_dependencies
    
    trap 'handle_error "repository"' ERR
    clone_repository
    
    trap 'handle_error "environment"' ERR
    setup_environment
    
    trap 'handle_error "virtualenv"' ERR
    setup_virtualenv
    
    trap 'handle_error "command"' ERR
    create_command
    
    # Reset error handling
    trap - ERR
    
    echo "Installation completed successfully!"
    echo "You can now use 'sudo keycloak-deploy --domain your-domain.com --email admin@example.com' to run the deployment"
}

main "$@"