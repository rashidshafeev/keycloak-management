# Keycloak Management: Testing and Installation Guide

This document explains how the Keycloak Management testing environment works and the installation flow of this tool.

## Installation Flow

The Keycloak Management tool is installed using the `install.sh` script, which performs several critical steps to set up the environment correctly.

### Installation Script Flow

1. **Initial Validation**
   - Checks if script is run as root
   - Parses command-line arguments: `--reset`, `--no-clone`, `--update`, `--help`

2. **Environment Setup**
   - Sets up logging to `/var/log/keycloak-install.log`
   - Installs git if not already present
   - Creates the installation directory (`/opt/fawz/keycloak` by default)

3. **Repository Management**
   - Clones the repository if not already present, or updates it if requested
   - Configures git to trust the installation directory
   - Copies environment file (`.env.kcmanage`) if available

4. **Module Loading and Execution**
   - Sources common functions from `prepare/common.sh`
   - Loads modules in specified order: cleanup.sh, command.sh, virtualenv.sh
   - If `--reset` is specified, runs the reset function and exits
   - Otherwise, sets up logging, loads state, backs up existing installation
   - Sets up Python virtual environment
   - Creates the `kcmanage` command wrapper

### Key Functions

- **`setup_logging`**: Initializes logging for the installation process
- **`load_state`**: Loads the current state of the installation
- **`backup_existing`**: Creates a backup of any existing installation
- **`setup_virtualenv`**: Creates and configures the Python virtual environment
- **`create_command`**: Creates the `kcmanage` system command

### Reset Process

When `--reset` is specified, the script:
1. Calls the `reset_installation` function from `cleanup.sh`
2. Removes virtual environment, configuration files, and command links
3. Returns the system to a clean state without removing the repository itself

## Testing Environment

The testing environment in `tests/deployment/` provides a containerized setup to test the installation and functionality of the Keycloak Management tool in isolation.

### Testing Environment Components

1. **`Dockerfile.test`**
   - Creates a minimal Debian environment
   - Installs base dependencies: sudo, git, curl
   - Serves as the foundation for testing

2. **`docker-compose.test.yml`**
   - Defines the test container service
   - Maps the installation script and environment files
   - Runs with privileged mode to simulate a real server

3. **`test-entrypoint.sh`**
   - First script executed when the container starts
   - Configures sudo access for root
   - Sets up Git credentials if provided
   - Runs the installation script
   - Keeps the container running for further testing

4. **`run-test-env.sh`**
   - Management script for the test environment
   - Supports different modes: normal start, rebuild, full rebuild
   - Provides user with commands for interacting with the test environment
   - Checks container status and displays logs if startup fails

### Test Environment Usage

The test environment is designed to be a isolated sandbox where you can test the Keycloak Management tool without affecting your actual system.

#### Starting the Test Environment

```bash
cd tests/deployment
./run-test-env.sh
```

This will:
1. Start the test container if it exists
2. Build and start a new container if it doesn't exist
3. Wait for services to be ready
4. Show available commands for interacting with the environment

#### Rebuilding the Test Environment

To rebuild the container without destroying data:
```bash
./run-test-env.sh --rebuild
```

For a complete clean start:
```bash
./run-test-env.sh --rebuild-all
```

#### Testing in the Environment

Once the environment is running, you can:
1. Enter the container shell:
   ```bash
   docker-compose -f docker-compose.test.yml exec vps-test bash
   ```

2. Run `kcmanage` commands directly:
   ```bash
   docker exec deployment-vps-test-1 kcmanage status
   docker exec deployment-vps-test-1 kcmanage deploy
   ```

3. View logs:
   ```bash
   docker-compose -f docker-compose.test.yml logs -f
   ```

## Dependency Architecture

The Keycloak Management tool has several layers of dependencies:

### System Dependencies

- Python 3.6+ with development headers
- OpenSSL development libraries (libssl-dev/openssl-devel)
- Git for version control
- Docker and Docker Compose (installed by the tool)

### Python Dependencies

- Click for CLI interface
- PyYAML for configuration
- Jinja2 for templating
- Docker SDK for Python
- Requests for HTTP communication
- PyOpenSSL for certificate management

## Diagnosing the OpenSSL Issue

The error "No module named 'OpenSSL'" indicates that:

1. Either the Python PyOpenSSL package isn't installed in the virtual environment
2. Or the system is missing OpenSSL development libraries needed for compilation

### Solutions

1. Install system dependencies:
   ```bash
   # On Debian/Ubuntu
   apt-get update
   apt-get install -y libssl-dev python3-dev

   # On RHEL/CentOS
   yum install -y openssl-devel python3-devel
   ```

2. Reinstall Python dependencies:
   ```bash
   cd /opt/fawz/keycloak
   source venv/bin/activate
   pip install pyOpenSSL
   ```

3. Verify installation:
   ```bash
   python -c "import OpenSSL; print(OpenSSL.__version__)"
   ```

## Adding More Verbose Logging

The changes we've implemented in the codebase include:

1. More detailed logging in `kcmanage/__init__.py`:
   - Debug-level logging with detailed formatting
   - Python environment information logging
   - Explicit checks for OpenSSL availability
   - Better error handling for command imports

2. Enhanced error handling in `kcmanage/commands/deploy.py`:
   - Step-by-step logging of each operation
   - Detailed dependency checking
   - Specific error messages for common issues
   - Command-line options for verbose output and dry runs

3. A comprehensive debugging guide in `docs/debugging-guide.md`:
   - Common issues and solutions
   - Diagnostic steps
   - Verification commands

These improvements should help identify the source of the OpenSSL issue and make future debugging easier.
