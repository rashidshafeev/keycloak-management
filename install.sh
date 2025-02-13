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
        
        # Create installation directory
        mkdir -p "${INSTALL_DIR}"
        
        # Clone repository
        if [ ! -d "${INSTALL_DIR}/.git" ]; then
            if ! git clone "${REPO_URL}" "${INSTALL_DIR}"; then
                echo "Error: Failed to clone repository"
                exit 1
            fi
            
            # Configure git to trust this directory
            if ! git config --global --get-all safe.directory | grep -q "^${INSTALL_DIR}\$"; then
                echo "Configuring git to trust ${INSTALL_DIR}..."
                git config --global --add safe.directory "${INSTALL_DIR}"
            fi
        else
            echo "Repository already exists, skipping clone..."
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
            # First try to find .env.example in the repository
            if [ -f "${INSTALL_DIR}/.env.example" ]; then
                ENV_EXAMPLE="${INSTALL_DIR}/.env.example"
            elif [ -f "$(dirname "$0")/.env.example" ]; then
                # If not in install dir, check script directory
                ENV_EXAMPLE="$(dirname "$0")/.env.example"
            else
                echo "Error: .env.example not found in ${INSTALL_DIR} or $(dirname "$0")"
                exit 1
            fi
            
            # Copy the found .env.example
            cp "${ENV_EXAMPLE}" "${INSTALL_DIR}/.env"
            
            # Generate secure passwords
            KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -base64 12)
            KEYCLOAK_DB_PASSWORD=$(openssl rand -base64 12)
            GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 12)
            WAZUH_REGISTRATION_PASSWORD=$(openssl rand -base64 12)
            GRAFANA_SMTP_PASSWORD=$(openssl rand -base64 12)
            
            # Get system hostname for domain suggestion
            HOSTNAME=$(hostname -f)
            
            # Prompt for required variables
            echo "Please provide the following required information:"
            echo "Press Enter to use the default value (shown in brackets)"
            echo
            
            # SMTP Configuration
            read -p "SMTP Host [smtp.gmail.com]: " SMTP_HOST
            SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}
            
            read -p "SMTP Port [587]: " SMTP_PORT
            SMTP_PORT=${SMTP_PORT:-587}
            
            read -p "SMTP User [alerts@example.com]: " SMTP_USER
            SMTP_USER=${SMTP_USER:-rashidshafeev@gmail.com}
            
            read -p "Alert Email Address [admin@example.com]: " ALERT_EMAIL
            ALERT_EMAIL=${ALERT_EMAIL:-rashidshafeev@gmail.com}
            
            # Slack Configuration
            read -p "Use Slack notifications? (y/N): " USE_SLACK
            if [[ $USE_SLACK =~ ^[Yy]$ ]]; then
                read -p "Slack Webhook URL: " SLACK_WEBHOOK
                read -p "Slack Channel [#alerts]: " SLACK_CHANNEL
                SLACK_CHANNEL=${SLACK_CHANNEL:-#alerts}
            else
                SLACK_WEBHOOK=""
                SLACK_CHANNEL="#alerts"
            fi
            
            # Firewall Configuration
            echo
            echo "Enter allowed admin IPs (comma-separated, e.g., 192.168.1.100,10.0.0.50)"
            echo "These IPs will have access to admin ports"
            read -p "Admin IPs [127.0.0.1]: " ADMIN_IPS
            ADMIN_IPS=${ADMIN_IPS:-127.0.0.1}
            
            # Update Keycloak settings
            sed -i "s/KEYCLOAK_ADMIN=.*/KEYCLOAK_ADMIN=admin/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_ADMIN_PASSWORD=.*/KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_DB_PASSWORD=.*/KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}/" "${INSTALL_DIR}/.env"
            
            # Update Docker settings
            sed -i "s/DOCKER_REGISTRY=.*/DOCKER_REGISTRY=docker.io/" "${INSTALL_DIR}/.env"
            sed -i "s/KEYCLOAK_VERSION=.*/KEYCLOAK_VERSION=latest/" "${INSTALL_DIR}/.env"
            sed -i "s/POSTGRES_VERSION=.*/POSTGRES_VERSION=latest/" "${INSTALL_DIR}/.env"
            
            # Update SSL settings (will be handled by deploy.py)
            sed -i "s#SSL_CERT_PATH=.*#SSL_CERT_PATH=/etc/letsencrypt/live/\${KEYCLOAK_DOMAIN}/fullchain.pem#" "${INSTALL_DIR}/.env"
            sed -i "s#SSL_KEY_PATH=.*#SSL_KEY_PATH=/etc/letsencrypt/live/\${KEYCLOAK_DOMAIN}/privkey.pem#" "${INSTALL_DIR}/.env"
            
            # Update Prometheus settings
            sed -i "s/PROMETHEUS_SCRAPE_INTERVAL=.*/PROMETHEUS_SCRAPE_INTERVAL=15s/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_EVAL_INTERVAL=.*/PROMETHEUS_EVAL_INTERVAL=15s/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_RETENTION_TIME=.*/PROMETHEUS_RETENTION_TIME=15d/" "${INSTALL_DIR}/.env"
            sed -i "s/PROMETHEUS_STORAGE_SIZE=.*/PROMETHEUS_STORAGE_SIZE=50GB/" "${INSTALL_DIR}/.env"
            
            # Update Grafana settings
            sed -i "s/GRAFANA_ADMIN_USER=.*/GRAFANA_ADMIN_USER=admin/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}/" "${INSTALL_DIR}/.env"
            
            # Update Grafana SMTP settings
            sed -i "s/GRAFANA_SMTP_ENABLED=.*/GRAFANA_SMTP_ENABLED=true/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_HOST=.*/GRAFANA_SMTP_HOST=${SMTP_HOST}/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_PORT=.*/GRAFANA_SMTP_PORT=${SMTP_PORT}/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_USER=.*/GRAFANA_SMTP_USER=${SMTP_USER}/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_PASSWORD=.*/GRAFANA_SMTP_PASSWORD=${GRAFANA_SMTP_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SMTP_FROM=.*/GRAFANA_SMTP_FROM=${SMTP_USER}/" "${INSTALL_DIR}/.env"
            
            # Update Grafana alert settings
            sed -i "s/GRAFANA_ALERT_EMAIL=.*/GRAFANA_ALERT_EMAIL=${ALERT_EMAIL}/" "${INSTALL_DIR}/.env"
            sed -i "s#GRAFANA_SLACK_WEBHOOK_URL=.*#GRAFANA_SLACK_WEBHOOK_URL=${SLACK_WEBHOOK}#" "${INSTALL_DIR}/.env"
            sed -i "s/GRAFANA_SLACK_CHANNEL=.*/GRAFANA_SLACK_CHANNEL=${SLACK_CHANNEL}/" "${INSTALL_DIR}/.env"
            
            # Update Wazuh settings
            sed -i "s/WAZUH_MANAGER_IP=.*/WAZUH_MANAGER_IP=localhost/" "${INSTALL_DIR}/.env"
            sed -i "s/WAZUH_REGISTRATION_PASSWORD=.*/WAZUH_REGISTRATION_PASSWORD=${WAZUH_REGISTRATION_PASSWORD}/" "${INSTALL_DIR}/.env"
            sed -i "s/WAZUH_AGENT_NAME=.*/WAZUH_AGENT_NAME=keycloak-${HOSTNAME}/" "${INSTALL_DIR}/.env"
            
            # Update Firewall settings
            sed -i "s/FIREWALL_MAX_BACKUPS=.*/FIREWALL_MAX_BACKUPS=5/" "${INSTALL_DIR}/.env"
            sed -i "s/FIREWALL_ALLOWED_PORTS=.*/FIREWALL_ALLOWED_PORTS=22,80,443,8080,8443,3000,9090,9100,9323/" "${INSTALL_DIR}/.env"
            sed -i "s/FIREWALL_ADMIN_IPS=.*/FIREWALL_ADMIN_IPS=${ADMIN_IPS}/" "${INSTALL_DIR}/.env"
            
            # Update Backup settings
            sed -i "s#BACKUP_STORAGE_PATH=.*#BACKUP_STORAGE_PATH=/opt/fawz/backup#" "${INSTALL_DIR}/.env"
            sed -i "s/BACKUP_RETENTION_DAYS=.*/BACKUP_RETENTION_DAYS=30/" "${INSTALL_DIR}/.env"
            
            # Update Logging settings
            sed -i "s/LOG_LEVEL=.*/LOG_LEVEL=INFO/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_FORMAT=.*/LOG_FORMAT=json/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_MAX_SIZE=.*/LOG_MAX_SIZE=100MB/" "${INSTALL_DIR}/.env"
            sed -i "s/LOG_MAX_FILES=.*/LOG_MAX_FILES=10/" "${INSTALL_DIR}/.env"
            
            echo
            echo "Environment file created with secure defaults."
            echo
            echo "IMPORTANT: Your generated passwords are:"
            echo "Keycloak Admin Password: ${KEYCLOAK_ADMIN_PASSWORD}"
            echo "Keycloak DB Password: ${KEYCLOAK_DB_PASSWORD}"
            echo "Grafana Admin Password: ${GRAFANA_ADMIN_PASSWORD}"
            echo "Wazuh Registration Password: ${WAZUH_REGISTRATION_PASSWORD}"
            echo "Please save these passwords in a secure location!"
            echo
            echo "Configuration Summary:"
            echo "SMTP Host: ${SMTP_HOST}"
            echo "SMTP Port: ${SMTP_PORT}"
            echo "SMTP User: ${SMTP_USER}"
            echo "Alert Email: ${ALERT_EMAIL}"
            echo "Slack Notifications: ${USE_SLACK}"
            if [[ $USE_SLACK =~ ^[Yy]$ ]]; then
                echo "Slack Channel: ${SLACK_CHANNEL}"
            fi
            echo "Admin IPs: ${ADMIN_IPS}"
            echo
            echo "You can modify these settings later by editing:"
            echo "${INSTALL_DIR}/.env"
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
        echo "Setting up Python virtual environment..."
        
        # Create and activate virtual environment
        cd "${INSTALL_DIR}"
        python3 -m venv venv
        source "${INSTALL_DIR}/venv/bin/activate"
        
        # Upgrade pip and setuptools
        python -m pip install --upgrade pip setuptools wheel
        
        # Install dependencies with retries and better error handling
        echo "Installing Python dependencies..."
        MAX_RETRIES=3
        RETRY_COUNT=0
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if pip install -r requirements.txt; then
                break
            fi
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
                echo "Error: Failed to install dependencies after $MAX_RETRIES attempts"
                deactivate
                exit 1
            fi
            echo "Retrying dependency installation (attempt $((RETRY_COUNT + 1)) of $MAX_RETRIES)..."
            sleep 2
        done
        
        # Verify critical dependencies
        echo "Verifying dependencies..."
        if ! python -c "import click, yaml, docker, requests" &> /dev/null; then
            echo "Error: Critical dependencies not installed properly"
            deactivate
            exit 1
        fi
        
        deactivate
        save_state "virtualenv"
    else
        echo "Virtual environment already set up, skipping..."
    fi
}

create_command() {
    if [[ -z "${completed_steps[command]}" ]]; then
        echo "Creating keycloak-deploy command..."
        
        # Create command file
        cat > /usr/local/bin/keycloak-deploy << 'EOF'
#!/bin/bash

INSTALL_DIR="/opt/fawz/keycloak"

# Check if virtual environment exists and dependencies are installed
check_dependencies() {
    if [ ! -f "${INSTALL_DIR}/venv/bin/activate" ]; then
        echo "Error: Virtual environment not found. Please run the installation script first."
        exit 1
    fi
    
    source "${INSTALL_DIR}/venv/bin/activate"
    
    echo "Verifying dependencies..."
    if ! python -c "import click, docker, requests" &> /dev/null; then
        echo "Error: Critical dependencies missing. Please run the installation script to fix."
        deactivate
        exit 1
    fi
    deactivate
}

# Check dependencies first
check_dependencies

# Activate virtual environment with full path
source "${INSTALL_DIR}/venv/bin/activate"

# Parse command line arguments
case "$1" in
    --domain)
        if [ -z "$2" ]; then
            echo "Error: --domain requires a domain name"
            exit 1
        fi
        DOMAIN="$2"
        shift 2
        ;;
    --help)
        echo "Usage: keycloak-deploy [OPTIONS]"
        echo
        echo "Options:"
        echo "  --domain DOMAIN    Domain name for Keycloak installation"
        echo "  --email EMAIL      Email for SSL certificate"
        echo "  --help            Show this help message"
        exit 0
        ;;
    *)
        if [ -z "$1" ]; then
            echo "Error: --domain is required"
            echo "Run 'keycloak-deploy --help' for usage"
            exit 1
        fi
        ;;
esac

# Change to installation directory
cd "${INSTALL_DIR}"

# Execute deployment script with all arguments
python deploy.py "$@"

# Deactivate virtual environment
deactivate

EOF
        
        # Make command executable
        chmod +x /usr/local/bin/keycloak-deploy
        
        save_state "command"
    else
        echo "Command already created, skipping..."
    fi
}

reset_installation() {
    echo "WARNING: This will remove all Keycloak components and configuration."
    echo "This includes:"
    echo "  - Docker containers and volumes"
    echo "  - Installation directory"
    echo "  - Configuration files"
    echo "  - SSL certificates"
    echo "  - Firewall rules"
    echo "  - Database data"
    read -p "Are you sure you want to continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Reset cancelled."
        exit 1
    fi

    echo "Performing reset..."
    
    # Stop and remove Docker containers without checking command existence
    docker-compose -f "${INSTALL_DIR}/docker-compose.yml" down -v 2>/dev/null || true
    docker system prune -f 2>/dev/null || true

    # Remove firewall rules without checking command existence
    ufw delete allow 8080/tcp 2>/dev/null || true
    ufw delete allow 8443/tcp 2>/dev/null || true
    ufw delete allow 9090/tcp 2>/dev/null || true
    ufw delete allow 3000/tcp 2>/dev/null || true

    # Remove all directories and files
    rm -rf "${INSTALL_DIR}" 2>/dev/null || true
    rm -rf "/opt/fawz/backup" 2>/dev/null || true
    rm -f /usr/local/bin/keycloak-deploy 2>/dev/null || true
    rm -f "${STATE_FILE}" 2>/dev/null || true

    echo "Reset completed successfully."
    exit 0
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
    if [[ "$1" == "--reset" ]]; then
        reset_installation
    fi

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