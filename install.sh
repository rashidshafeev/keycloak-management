#!/bin/bash

# Configuration
REPO_URL="https://github.com/yourusername/keycloak-management.git"
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