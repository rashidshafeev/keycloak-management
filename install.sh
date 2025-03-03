#!/bin/bash

# Check root first
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# Parse command line arguments
RESET=0
NO_CLONE=false
UPDATE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=1
            shift
            ;;
        --no-clone)
            NO_CLONE=true
            shift
            ;;
        --update)
            UPDATE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --reset               Reset the installation"
            echo "  --no-clone            Do not clone the repository"
            echo "  --update              Update the installation (git pull)"
            echo "  --verbose             Enable verbose output"
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
LOG_FILE="/var/log/keycloak-install.log"

# Setup logging
mkdir -p "$(dirname "$LOG_FILE")"
if [ "$VERBOSE" = true ]; then
    # More verbose logging
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    set -x  # Enable debug mode to show each command
else
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
fi

echo "======================================================"
echo "Starting Keycloak Management installation at $(date)"
echo "======================================================"

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
    elif [ "$UPDATE" = "true" ]; then
        echo "Repository exists, updating..."
        cd "${INSTALL_DIR}"
        git pull
    fi
fi

# Check for .env.kcmanage in the current directory
if [ -f ".env.kcmanage" ]; then
    echo "Found .env.kcmanage, copying to repository..."
    cp .env.kcmanage "${INSTALL_DIR}/.env"
    chmod 600 "${INSTALL_DIR}/.env"  # Secure file permissions
fi

# Set up scripts directory path
PREPARE_DIR="${INSTALL_DIR}/prepare"

# Change to installation directory
cd "${INSTALL_DIR}"

# Source common functions
if [ -f "${PREPARE_DIR}/common.sh" ]; then
    echo "Loading common functions..."
    source "${PREPARE_DIR}/common.sh"
else
    echo "ERROR: common.sh not found in ${PREPARE_DIR}"
    exit 1
fi

# Check system dependencies first
if [ -f "${PREPARE_DIR}/system_deps.sh" ]; then
    echo "Checking system dependencies..."
    source "${PREPARE_DIR}/system_deps.sh"
    if ! install_system_dependencies; then
        echo "ERROR: Failed to install system dependencies"
        exit 1
    fi
else
    echo "WARNING: system_deps.sh not found, skipping dependency check"
fi

# Load modules in specific order
modules=(
    "cleanup.sh"
    "command.sh"
    "virtualenv.sh"
)

for module in "${modules[@]}"; do
    module_path="${PREPARE_DIR}/${module}"
    if [ -f "$module_path" ]; then
        echo "Loading module: $module"
        source "$module_path"
    else
        echo "Warning: Module $module not found in ${PREPARE_DIR}"
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
echo "Setting up Python virtual environment..."
if ! setup_virtualenv; then
    echo "ERROR: Failed to set up Python virtual environment"
    exit 1
fi

echo "Creating kcmanage command..."
if ! create_command; then
    echo "ERROR: Failed to create kcmanage command"
    exit 1
fi

# Remove error trap
trap - ERR

# Test the installation
echo "Testing installation..."
if command -v kcmanage &> /dev/null; then
    echo "kcmanage command is available"
    
    # Test basic Python imports
    echo "Testing Python environment..."
    source "${INSTALL_DIR}/venv/bin/activate"
    
    PYTHON_TEST=$(python3 -c "import sys; print('Python path:', sys.path); print('Python version:', sys.version); try: import ssl; print('SSL version:', ssl.OPENSSL_VERSION); except ImportError as e: print('SSL import error:', e); try: import OpenSSL; print('PyOpenSSL version:', OpenSSL.__version__); except ImportError as e: print('PyOpenSSL import error:', e);" 2>&1)
    
    echo "Python environment test results:"
    echo "$PYTHON_TEST"
    
    if echo "$PYTHON_TEST" | grep -q "PyOpenSSL import error"; then
        echo "WARNING: PyOpenSSL module is not available. Some features may not work correctly."
        echo "Try running: pip install pyOpenSSL"
    fi
else
    echo "WARNING: kcmanage command is not available. Installation may have failed."
fi

echo "====================================================="
echo "Installation completed at $(date)"
echo "====================================================="
echo "You can now use 'kcmanage' command to manage your Keycloak deployment."
echo
echo "Available commands:"
echo "  kcmanage setup     - Initial setup and configuration"
echo "  kcmanage deploy    - Deploy Keycloak"
echo "  kcmanage status    - Check deployment status"
echo "  kcmanage backup    - Create a backup"
echo "  kcmanage restore   - Restore from backup"
echo "  kcmanage update    - Update the software (git pull)"
echo
echo "To reset the installation, run:"
echo "  $0 --reset"
echo
echo "For troubleshooting information, see the documentation:"
echo "  ${INSTALL_DIR}/docs/debugging-guide.md"
echo "====================================================="
