# Installation Process Documentation

## Overview
The installation process is managed by `install.sh` which orchestrates several specialized scripts to set up Keycloak and related services.

## Installation Scripts Structure

```
scripts/
├── db_backup.sh              # Database backup functionality
└── install/                  # Installation scripts
    ├── cleanup.sh           # Cleanup and reset functions
    ├── command.sh          # Creates keycloak-deploy command
    ├── common.sh           # Shared functions and variables
    ├── dependencies.sh     # System dependencies installation
    ├── environment.sh      # Environment setup and configuration
    ├── system_checks.sh    # System requirements verification
    └── virtualenv.sh       # Python virtual environment setup
```

## Script Functions

### 1. common.sh
- **Purpose**: Provides shared functions and variables used across all scripts
- **Key Functions**:
  - `setup_logging`: Configures logging
  - `save_state`: Saves installation state
  - `load_state`: Loads previous installation state
  - `handle_error`: Error handling
  - `clone_repository`: Repository management
  - `reset_installation`: Installation reset

### 2. system_checks.sh
- **Purpose**: Verifies system requirements
- **Key Functions**:
  - `check_root`: Ensures script runs as root
  - `check_system`: Validates OS compatibility and required commands

### 3. dependencies.sh
- **Purpose**: Manages system package installation
- **Key Functions**:
  - `install_dependencies`: Installs required packages based on OS
  - Handles:
    - Python packages
    - Docker and Docker Compose
    - System utilities

### 4. environment.sh
- **Purpose**: Sets up environment configuration
- **Key Functions**:
  - `generate_secure_password`: Generates random passwords
  - `prompt_for_variables`: Interactive configuration
  - `check_required_variables`: Validates required settings
  - `setup_environment`: Configures environment variables

### 5. virtualenv.sh
- **Purpose**: Python virtual environment management
- **Key Functions**:
  - `setup_virtualenv`: Creates and configures Python virtual environment
  - Installs Python dependencies from requirements.txt

### 6. command.sh
- **Purpose**: Creates management command
- **Key Functions**:
  - `create_command`: Creates keycloak-deploy command
  - Sets up command in /usr/local/bin

### 7. cleanup.sh
- **Purpose**: Handles cleanup and backup operations
- **Key Functions**:
  - `cleanup_repository`: Cleans repository
  - `cleanup_command`: Removes command
  - `backup_existing`: Creates backups
  - `reset_installation`: Full reset functionality

## Installation Flow

1. **Initial Setup** (`install.sh`):
   ```bash
   # Check root access
   # Parse command line arguments
   # Set up logging
   # Clone repository
   ```

2. **System Preparation**:
   ```bash
   # Check system requirements
   check_root
   check_system
   
   # Install dependencies
   install_dependencies
   ```

3. **Environment Setup**:
   ```bash
   # Configure environment
   setup_environment
   
   # Set up Python environment
   setup_virtualenv
   ```

4. **Command Creation**:
   ```bash
   # Create management command
   create_command
   ```

## State Management

The installation process maintains state to:
- Track completed steps
- Enable resuming interrupted installations
- Support clean rollbacks

State is stored in: `/opt/fawz/.install_state`

## Configuration Files

Key configuration files:
- `/etc/keycloak/config.yaml`: Main configuration
- `requirements.txt`: Python dependencies
- Environment-specific configurations in `config/environments/`

## Usage

Basic installation:
```bash
./install.sh --domain example.com --email admin@example.com
```

Reset installation:
```bash
./install.sh --reset
