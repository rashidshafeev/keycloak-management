# Testing Environment

This directory contains the testing setup for the Keycloak Management project.

## Overview

The testing environment is designed to simulate a real VPS deployment scenario where a user would:
1. Copy the install.sh script to their server
2. Make it executable
3. Run it to set up Keycloak and related services

## Directory Structure

```
tests/
├── deployment/           # Docker-based test environment
│   ├── Dockerfile.test  # Test container definition
│   ├── docker-compose.test.yml
│   └── test-entrypoint.sh
└── config/              # Configuration tests
    ├── test_authentication.py
    ├── test_clients.py
    ├── test_events.py
    └── test_integration.py
```

## Test Environment

The test environment uses Docker to simulate a clean VPS environment:
- Base image: debian:bullseye-slim
- Required packages pre-installed
- Privileged mode for system operations

### Flow Simulation

The test environment simulates the following user flow:

```
Real VPS Environment          Test Environment
--------------------         -----------------
1. Copy install.sh     -->   1. Mount install.sh
2. Make executable     -->   2. Make executable
3. Run install.sh     -->   3. Run install.sh
   - Clones repo            - Clones repo
   - Sets up env           - Sets up env
   - Installs deps         - Installs deps
   - Configures system     - Configures system
```

## Running Tests

To run the test environment:

```bash
cd tests/deployment
docker-compose -f docker-compose.test.yml up --build
```

This will:
1. Build the test container
2. Mount the install script
3. Run the installation process
4. Verify the setup

## Test Cases

The test environment verifies:
- Installation on fresh system
- Dependency installation
- Repository cloning
- Environment setup
- Virtual environment creation
- System configuration
- Error handling and rollback

## Configuration Tests

The `config/` directory contains Python unit tests for various configuration aspects:
- Authentication configuration
- Client management
- Event handling
- Integration tests
