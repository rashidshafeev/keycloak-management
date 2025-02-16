#!/bin/bash

# Check root first
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# Parse command line arguments
RESET=0
NO_CLONE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=1
            shift
            ;;
        --domain)
            export KEYCLOAK_DOMAIN="$2"
            shift 2
            ;;
        --email)
            export ADMIN_EMAIL="$2"
            shift 2
            ;;
        --no-clone)
            NO_CLONE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --reset               Reset the installation"
            echo "  --domain DOMAIN       Domain for Keycloak (default: system hostname)"
            echo "  --email EMAIL         Admin email (default: admin@hostname)"
            echo "  --no-clone            Do not clone the repository"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Initial configuration
REPO_URL="https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git"
INSTALL_DIR="/opt/fawz/keycloak"
SCRIPTS_DIR="$(dirname "$0")/scripts/install"
LOG_FILE="/var/log/keycloak-install.log"

# Setup logging
mkdir -p "$(dirname "$LOG_FILE")"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)
echo "Starting installation at $(date)"

# Check and install git if needed
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing..."
    apt-get update
    apt-get install -y git
fi

# Create installation directory
mkdir -p "${INSTALL_DIR}"

# Clone or update repository
if [ "$NO_CLONE" != "true" ]; then
    if [ ! -d "${INSTALL_DIR}/.git" ]; then
        echo "Cloning repository..."
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
        echo "Repository exists, updating..."
        cd "${INSTALL_DIR}"
        git pull
    fi
fi

# Source all installation modules in specific order
echo "Loading installation modules..."
# First load common.sh as it contains shared functions and variables
source "${SCRIPTS_DIR}/common.sh"

# Then load other modules in specific order
modules=(
    "cleanup.sh"
    "command.sh"
    "dependencies.sh"
    "environment.sh"
    "system_checks.sh"
    "virtualenv.sh"
)

for module in "${modules[@]}"; do
    module_path="${SCRIPTS_DIR}/${module}"
    if [ -f "$module_path" ]; then
        echo "Loading module: $module"
        source "$module_path"
    fi
done

# Handle reset if requested
if [ $RESET -eq 1 ]; then
    echo "Reset flag detected. Resetting installation..."
    if ! reset_installation; then
        echo "Reset failed!"
        exit 1
    fi
    exit 0
fi

# Run installation steps
echo "Starting installation process..."
setup_logging
load_state

# Backup existing installation if present and not resetting
if [ $RESET -eq 0 ]; then
    backup_existing
fi

# Trap for cleanup on error
trap 'handle_error $? "Installation failed" "main"' ERR

# Run installation steps
check_root
check_system
install_dependencies
clone_repository
setup_environment
setup_virtualenv
create_command

# Remove error trap
trap - ERR

echo "Installation completed successfully!"
echo "You can now use 'keycloak-deploy' command to manage your Keycloak deployment."
echo
echo "Domain: ${KEYCLOAK_DOMAIN}"
echo "Admin Email: ${ADMIN_EMAIL}"
echo
echo "To reset the installation, run:"
echo "  $0 --reset"
