#!/bin/bash
# Check root first
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# Parse command line arguments
RESET=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=1
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --reset     Reset the installation"
            echo "  --help      Show this help message"
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
INSTALL_DIR="${INSTALL_DIR:-/opt/fawz/keycloak}"
VENV_DIR="${INSTALL_DIR}/venv"
STATE_FILE="${INSTALL_DIR}/.install_state"
export INSTALL_DIR VENV_DIR STATE_FILE

# Create installation directory
mkdir -p "${INSTALL_DIR}"

# Set up scripts directory path
SCRIPTS_DIR="./prepare"

# Source common functions
source "${SCRIPTS_DIR}/common.sh"

# Load modules in specific order
modules=(
    "cleanup.sh"
    "virtualenv.sh"
    "command.sh"
)

for module in "${modules[@]}"; do
    module_path="${SCRIPTS_DIR}/${module}"
    if [ -f "$module_path" ]; then
        echo "Loading module: $module"
        source "$module_path"
    else
        echo "Warning: Module $module not found in ${SCRIPTS_DIR}"
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
echo "Starting installation at $(date)"

# Backup existing installation if present and not resetting
if [ $RESET -eq 0 ]; then
    backup_existing
fi

# Trap for cleanup on error
trap 'handle_error $? "Installation failed" "main"' ERR

# Run installation steps
setup_virtualenv
create_command

# Remove error trap
trap - ERR

echo "Installation completed successfully!"
echo "You can now use 'kcmanage' command to manage your Keycloak deployment."
echo
echo "Available commands:"
echo "  kcmanage setup     - Initial setup and configuration"
echo "  kcmanage deploy    - Deploy Keycloak"
echo "  kcmanage status    - Check deployment status"
echo "  kcmanage backup    - Create a backup"
echo "  kcmanage restore   - Restore from backup"
echo
echo "To reset the installation, run:"
echo "  $0 --reset"
