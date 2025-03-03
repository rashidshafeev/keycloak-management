# Keycloak Management Debugging Guide

## Common Issues and Solutions

### "No module named 'OpenSSL'" Error

This error occurs when the Python OpenSSL module is missing. The OpenSSL module is required for secure connections and certificate operations.

#### Diagnosis Steps

1. Check if the Python environment has the required dependencies:
   ```bash
   # From your Docker test container
   cd /opt/fawz/keycloak
   source venv/bin/activate  # Assuming venv is your virtual environment name
   pip list | grep -i openssl
   ```

2. Check if the system has the OpenSSL development libraries:
   ```bash
   # For Debian/Ubuntu
   dpkg -l | grep libssl-dev
   
   # For RHEL/CentOS
   rpm -qa | grep openssl-devel
   ```

#### Solution

Install the necessary system packages and then reinstall the Python dependencies:

```bash
# For Debian/Ubuntu
apt-get update
apt-get install -y libssl-dev

# For RHEL/CentOS
yum install -y openssl-devel

# Then reinstall Python dependencies
cd /opt/fawz/keycloak
source venv/bin/activate
pip install -r requirements.txt
```

### Python Import Errors

If you see import errors like "No module named 'src.core.orchestrator'", the Python path might not be set correctly.

#### Diagnosis

Check your Python path:
```bash
cd /opt/fawz/keycloak
source venv/bin/activate
python -c "import sys; print(sys.path)"
```

Ensure the base directory is in the Python path:
```bash
cd /opt/fawz/keycloak
source venv/bin/activate
python -c "import os; print(os.getcwd() in sys.path)"
```

#### Solution

Update the Python path in your environment setup:
```bash
# Add to your virtualenv activation script
export PYTHONPATH=/opt/fawz/keycloak:$PYTHONPATH
```

## Testing Environment Guide

The `tests/deployment` directory contains a testing environment to validate deployments in a containerized setting. This allows you to test the installation and functionality of the Keycloak Management tool without affecting your actual system.

### Test Environment Components

1. **Dockerfile.test**: Creates a minimal Debian environment with necessary tools
2. **docker-compose.test.yml**: Sets up the test container with proper mounts
3. **test-entrypoint.sh**: Initial script that runs in the container
4. **run-test-env.sh**: Script to manage the test environment
5. **.env.test**: Sample environment variables for testing

### How to Use the Test Environment

1. Start the test environment:
   ```bash
   cd tests/deployment
   ./run-test-env.sh
   ```

2. Rebuild if needed:
   ```bash
   ./run-test-env.sh --rebuild
   ```

3. Full rebuild (clean start):
   ```bash
   ./run-test-env.sh --rebuild-all
   ```

4. Access the running container:
   ```bash
   docker-compose -f docker-compose.test.yml exec vps-test bash
   ```

5. Run tests inside the container:
   ```bash
   # Inside the container
   kcmanage status
   kcmanage deploy
   ```

## Adding More Verbose Logging

To add more detailed logging to help diagnose issues:

1. Update `kcmanage/__init__.py` to use DEBUG level logging
2. Add detailed exception handling in command modules
3. Add debugging output to key installation scripts

Example for a shell script (`prepare/virtualenv.sh`):
```bash
setup_virtualenv() {
    echo "Setting up Python virtual environment..."
    
    # Debug: Output Python version
    python3 --version
    
    # Debug: Check for system dependencies
    if command -v dpkg >/dev/null 2>&1; then
        echo "Checking for OpenSSL development libraries..."
        dpkg -l | grep libssl-dev
    elif command -v rpm >/dev/null 2>&1; then
        echo "Checking for OpenSSL development libraries..."
        rpm -qa | grep openssl-devel
    fi
    
    # Create virtual environment with verbose output
    python3 -m venv venv --verbose
    
    # Activate and upgrade pip with verbose output
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Upgrading pip..."
    pip install --upgrade pip -v
    
    echo "Installing dependencies..."
    pip install -r requirements.txt -v
    
    # Debug: List installed packages
    echo "Installed packages:"
    pip list
    
    echo "Virtual environment setup complete."
}
```

This enhanced debugging guide and logging improvements should help diagnose and fix the OpenSSL issue and similar problems that might arise during deployment.
