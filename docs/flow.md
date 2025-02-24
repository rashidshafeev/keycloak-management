# Installation Script Flow Documentation

## Overview
The `install.sh` script is the main installation script that orchestrates the setup and deployment of the Keycloak management system. This document outlines the flow and key components of the installation process.

## Command Line Arguments
The script accepts the following arguments:
- `--reset`: Triggers a reset of the installation
- `--no-clone`: Skips the repository cloning step
- `--help`: Displays usage information

## Key Variables
- `REPO_URL`: Git repository URL
- `INSTALL_DIR`: Installation directory (`/opt/fawz/keycloak`)
- `LOG_FILE`: Log file path (`/var/log/keycloak-install.log`)
- `SCRIPTS_DIR`: Directory containing installation modules (`${INSTALL_DIR}/scripts/install`)

## Installation Flow

### 1. Initial Checks and Setup
1. Root privilege check
2. Command line argument parsing
3. Git availability check and installation if needed
4. Installation directory creation
5. Logging setup

### 2. Repository Management
1. If `--no-clone` is not set:
   - Clone repository if not exists
   - Update repository if exists
   - Configure git trust settings for the directory
2. Copy `.env.kcmanage` to `.env` if present

### 3. Module Loading
The script loads the following modules in order:
1. `common.sh`: Common functions and utilities
2. `cleanup.sh`: Cleanup functionality
3. `command.sh`: Command setup
4. `dependencies.sh`: System dependencies
5. `virtualenv.sh`: Python virtual environment setup

### 4. Installation Process
1. Reset handling (if `--reset` flag is present)
   - Calls `reset_installation` function
   - Exits after reset

2. Main Installation Steps:
   - Setup logging
   - Load state
   - Backup existing installation (if not resetting)
   - Setup error handling trap
   - Setup virtual environment
   - Create command
   - Remove error trap

### 5. Final Steps
- Display success message
- Show available commands:
  - `kcmanage setup`
  - `kcmanage deploy`
  - `kcmanage status`
  - `kcmanage backup`
  - `kcmanage restore`

## Error Handling
- The script uses trap mechanism for error handling
- Errors are logged to `/var/log/keycloak-install.log`
- Installation state is preserved for debugging

## Module Dependencies

### common.sh
- Provides shared functions used by other modules
- Handles logging and state management

### cleanup.sh
- Manages installation cleanup
- Handles reset functionality

### command.sh
- Sets up the `kcmanage` command
- Configures command line interface

### dependencies.sh
- Manages system dependencies
- Handles package installation

### virtualenv.sh
- Sets up Python virtual environment
- Manages Python dependencies

## Security Considerations
1. Root privileges required
2. Secure file permissions for `.env` file (600)
3. Git directory trust configuration
4. Backup functionality for existing installations

## Notes
- The script maintains an installation log at `/var/log/keycloak-install.log`
- All operations are logged for debugging purposes
- The script can be safely re-run
- Reset functionality is available for clean reinstallation

# Deployment Flow Documentation

## Main Deployment Script (deploy.py)

### Overview
The `deploy.py` script serves as the main command-line interface for managing Keycloak deployment. It provides several essential commands for setup, deployment, status checking, backup, and restoration operations.

### Key Components

#### Environment Management
1. `init_environment()` function:
   - Checks for existing `.env` file
   - Validates required environment variables:
     - KEYCLOAK_DOMAIN
     - KEYCLOAK_ADMIN_EMAIL
     - KEYCLOAK_ADMIN_PASSWORD
     - DB_PASSWORD
   - Triggers setup process if configuration is missing
   - Loads and validates environment configuration

#### CLI Commands

1. `setup` command:
   - Verifies system requirements
   - Installs necessary dependencies
   - Configures environment variables
   - Sets up initial configuration

2. `deploy` command:
   - Validates system requirements
   - Initializes environment configuration
   - Uses DeploymentOrchestrator for actual deployment
   - Handles deployment process and error reporting

3. `status` command:
   - Checks system readiness
   - Verifies environment configuration
   - (Placeholder for status check implementation)

4. `backup` command:
   - Ensures system is ready
   - Validates environment
   - (Placeholder for backup implementation)

5. `restore` command:
   - Validates system state
   - Checks environment configuration
   - (Placeholder for restore implementation)

### Dependencies
The script relies on several key modules:
- `src.deployment.orchestrator`: Handles deployment orchestration
- `src.utils.system_checks`: Ensures system requirements
- `src.utils.environment`: Manages environment configuration

### Error Handling
- Comprehensive error catching and reporting
- User-friendly error messages via click.echo
- Proper exit codes for different failure scenarios

### Security Features
- Environment variable validation
- System requirement checks
- Secure password handling

### Usage Flow
1. User invokes command (setup/deploy/status/backup/restore)
2. System requirements are verified
3. Environment is initialized/validated
4. Requested operation is performed
5. Success/failure status is reported

## Deployment Orchestration (orchestrator.py)

### Overview
The `DeploymentOrchestrator` class manages the complete deployment process of Keycloak and its supporting components. It coordinates multiple deployment steps in a specific order, ensuring each component is properly configured and integrated.

### Deployment Steps
The orchestrator executes the following steps in sequence:

1. **System Preparation** (`SystemPreparationStep`)
   - Prepares the base system for deployment
   - Configures system requirements
   - Sets up necessary directories and permissions

2. **Docker Setup** (`DockerSetupStep`)
   - Ensures Docker is installed and configured
   - Sets up required Docker networks
   - Configures Docker volumes

3. **Certificate Management** (`CertificateManager`)
   - Handles SSL/TLS certificate setup
   - Manages certificate renewal
   - Configures secure communications

4. **Keycloak Deployment** (`KeycloakDeploymentStep`)
   - Deploys Keycloak containers
   - Configures database connections
   - Sets up initial admin credentials

5. **Keycloak Configuration** (`KeycloakConfigurationManager`)
   - Applies realm configurations
   - Sets up authentication flows
   - Configures clients and roles
   - Manages identity providers

6. **Monitoring Setup** (`PrometheusManager`)
   - Deploys Prometheus for metrics collection
   - Configures monitoring endpoints
   - Sets up alerting rules

7. **Database Backup** (`DatabaseBackupStep`)
   - Configures backup procedures
   - Sets up backup scheduling
   - Manages backup retention

### Installation Summary Generation
The orchestrator generates a comprehensive installation summary including:
- Installation date and configuration
- Service access information
- Security credentials
- SSL certificate details
- Backup configuration
- Service status information
- System paths and configurations
- Monitoring setup details

### Key Features

#### Error Handling
- Context-based error management
- Step-specific cleanup procedures
- Detailed error logging
- Rollback capabilities

#### Configuration Management
- Environment-based configuration
- Secure credential handling
- Service-specific configurations
- Backup and monitoring settings

#### Security Measures
- SSL/TLS certificate management
- Secure password handling
- Firewall configuration
- Access control setup

### Deployment Variables
Key configuration variables managed by the orchestrator:

1. **Keycloak Configuration**
   - KEYCLOAK_DOMAIN
   - KEYCLOAK_PORT
   - KEYCLOAK_ADMIN
   - KEYCLOAK_ADMIN_PASSWORD

2. **Database Settings**
   - DB_HOST
   - DB_PORT
   - DB_NAME
   - DB_USER
   - DB_PASSWORD

3. **Monitoring Configuration**
   - PROMETHEUS_DATA_DIR
   - GRAFANA_ADMIN_USER
   - GRAFANA_ADMIN_PASSWORD
   - GRAFANA_ALERT_EMAIL

4. **Security Settings**
   - SSL_CERT_PATH
   - SSL_KEY_PATH
   - FIREWALL_ALLOWED_PORTS
   - FIREWALL_ADMIN_IPS

5. **Backup Configuration**
   - BACKUP_STORAGE_PATH
   - BACKUP_TIME
   - BACKUP_RETENTION_DAYS

### Deployment Process Flow
1. Initialize orchestrator with configuration
2. Validate and prepare system requirements
3. Execute deployment steps in sequence
4. Generate installation summary
5. Verify deployment success
6. Enable monitoring and backup systems

## Detailed Deployment Steps

### 1. System Preparation (prepare.py)

#### Overview
The `SystemPreparationStep` class handles the initial system preparation by ensuring all required base packages are installed and the system is ready for Keycloak deployment.

#### Core Functionality

1. **Required Packages**
   The step ensures the following essential packages are installed:
   - `apt-transport-https`: For secure package transport
   - `ca-certificates`: For SSL/TLS certificate handling
   - `curl`: For network requests
   - `gnupg`: For package verification

2. **Completion Check**
   - Verifies if all required packages are already installed
   - Uses `dpkg -l` to check package installation status
   - Returns `True` only if all packages are properly installed

3. **Execution Process**
   - Updates package repository (`apt-get update`)
   - Installs all required packages
   - Handles installation errors and logging

#### Error Handling
- Captures and logs package installation failures
- No cleanup required (can_cleanup=False) as system packages should remain
- Returns False on any installation failure

#### Integration Points
- First step in the deployment chain
- Prepares system for Docker installation
- Sets up basic SSL/TLS capabilities
- Enables secure package management

### 2. Docker Setup (docker.py)

#### Overview
The `DockerSetupStep` class manages Docker installation, configuration, and resource setup required for Keycloak deployment.

#### Core Components

1. **Docker Installation**
   - Automatically installs Docker if not present
   - Uses official Docker installation script
   - Configures Docker service to start on boot
   - Verifies Docker daemon is responsive

2. **Network Configuration**
   - Creates dedicated `keycloak-network` bridge network
   - Configuration details:
     - Subnet: 172.20.0.0/16
     - Bridge name: keycloak-br0
     - Enabled container intercommunication
     - Configured IP masquerading
     - Custom labels for identification

3. **Volume Management**
   Creates and manages required Docker volumes:
   - `keycloak-data`: For Keycloak server data
     - Labels: app=keycloak, component=server
   - `postgres-data`: For database persistence
     - Labels: app=keycloak, component=database

#### Operational Flow

1. **Completion Check**
   - Verifies Docker daemon status
   - Confirms network existence
   - Validates volume presence
   - Returns status of infrastructure readiness

2. **Execution Process**
   - Ensures Docker is installed and running
   - Creates network if not exists
   - Sets up required volumes
   - Configures networking options
   - Labels resources for management

3. **Cleanup Capabilities**
   - Removes created volumes
   - Cleans up network configuration
   - Handles resource cleanup errors
   - Logs cleanup operations

#### Error Handling
- Comprehensive error catching
- Detailed logging of failures
- Graceful cleanup on failures
- Resource existence verification

#### Integration Points
- Provides container infrastructure
- Enables service isolation
- Ensures data persistence
- Supports service discovery

### 3. Certificate Management (ssl.py)

#### Overview
The `CertificateManager` class handles SSL/TLS certificate management for secure communications, including automated certificate acquisition, validation, backup, and renewal.

#### Core Components

1. **Certificate Configuration**
   - Main domain and additional domains support
   - Certificate paths management
   - Backup directory configuration
   - Validity period monitoring
   - Auto-renewal settings

2. **Certificate Validation**
   - Comprehensive certificate checks:
     - Expiration verification
     - Domain matching
     - Private key correspondence
     - Certificate chain validation
     - Minimum validity period (default: 30 days)

3. **Backup Management**
   - Automated backup rotation
   - Configurable maximum backups (default: 5)
   - Backup validation
   - Timestamp-based organization
   - Backup information logging

4. **Auto-Renewal**
   - Certbot integration
   - Automated renewal scheduling
   - Service-aware renewal hooks
   - Cron job configuration

#### Operational Flow

1. **Certificate Acquisition**
   - Certbot installation check
   - Domain validation
   - Certificate request handling
   - Staging environment support
   - Backup before changes

2. **Certificate Management**
   - Regular validity checks
   - Automated renewal triggers
   - Backup creation and rotation
   - Permission management
   - Service notifications

3. **Error Recovery**
   - Automatic backup restoration
   - Validation failure handling
   - Chain verification
   - Detailed error logging

#### Security Features
- Strict permission controls
- Chain of trust verification
- Private key protection
- Secure backup management
- Service-integrated renewal

#### Integration Points
- Let's Encrypt integration
- Keycloak service coordination
- System-wide certificate management
- Monitoring system integration

#### File Locations
- Certificates: `/etc/letsencrypt/live/<domain>/`
- Archives: `/etc/letsencrypt/archive/`
- Backups: `/opt/fawz/keycloak/certs/backup/`
- Renewal configuration: `/etc/cron.d/certbot-renew`

### 4. Keycloak Deployment (deploy.py)

#### Overview
The `KeycloakDeploymentStep` class manages the deployment of Keycloak and its required PostgreSQL database using Docker containers. It handles container configuration, health monitoring, and resource management.

#### Core Components

1. **PostgreSQL Configuration**
   - Image: postgres:15
   - Persistent volume mounting
   - Health monitoring
   - Resource limits:
     - CPU shares: 2
     - Memory limit: 1GB
     - Memory reservation: 512MB
   - Automatic restart policy

2. **Keycloak Configuration**
   - Image: quay.io/keycloak/keycloak:latest
   - Data persistence
   - Health checks
   - Resource allocation:
     - CPU shares: 4
     - Memory limit: 2GB
     - Memory reservation: 1GB
   - Port mappings: 8080, 8443

3. **Environment Configuration**
   - Database settings
   - Admin credentials
   - Event listeners
   - Performance tuning:
     - HTTP max connections
     - Proxy settings
     - Path configuration
     - Hostname validation

#### Deployment Process

1. **Container Preparation**
   - Image pulling
   - Network configuration
   - Volume mounting
   - Environment variable setup

2. **Database Deployment**
   - PostgreSQL container launch
   - Health check monitoring
   - Connection verification
   - Database initialization

3. **Keycloak Launch**
   - Container deployment
   - Service health monitoring
   - Response verification
   - Configuration application

#### Health Monitoring

1. **PostgreSQL Health Checks**
   - Command: `pg_isready`
   - Interval: 10 seconds
   - Timeout: 5 seconds
   - Maximum retries: 5

2. **Keycloak Health Checks**
   - Endpoint: `/health/ready`
   - Interval: 30 seconds
   - Timeout: 10 seconds
   - Maximum retries: 3

#### Error Handling
- Container health verification
- Startup timeout management
- Graceful cleanup on failure
- Detailed error logging
- Resource cleanup procedures

#### Integration Features
- Event listener configuration
- Webhook integration
- Database connection management
- Network isolation
- Resource monitoring

#### Cleanup Procedures
- Graceful container shutdown
- Resource cleanup
- Network cleanup
- Volume preservation
- 30-second shutdown timeout

### 5. Keycloak Configuration Management (configuration.py)

#### Overview
The `KeycloakConfigurationManager` class handles the systematic configuration of Keycloak using YAML templates. It manages multiple configuration aspects through a modular, dependency-aware approach.

#### Configuration Components

1. **Core Components** (Required)
   - Realm Configuration
     - Basic realm settings
     - Schema: realm_schema.json
   - Security Settings
     - Security policies
     - Schema: security_schema.json
   - Client Applications
     - Client configurations
     - Dependencies: realm
     - Schema: clients_schema.json
   - Role Definitions
     - Role mappings
     - Dependencies: realm
     - Schema: roles_schema.json
   - Authentication
     - Auth flows
     - Dependencies: realm, security
     - Schema: authentication_schema.json
   - Events
     - Event listeners
     - Schema: events_schema.json

2. **Optional Components**
   - Monitoring
     - Metrics configuration
     - Health checks
     - Schema: monitoring_schema.json
   - Themes
     - Custom theme settings
     - Schema: themes_schema.json
   - SMTP
     - Email configuration
     - Schema: smtp_schema.json

#### Configuration Process

1. **Template Loading**
   - YAML configuration loading
   - Schema validation
   - Dependency resolution
   - Configuration caching

2. **Configuration Order**
   - Required components first
   - Dependency-based ordering
   - Optional components last
   - Interactive configuration support

3. **Validation**
   - Schema-based validation
   - Dependency checking
   - Configuration verification
   - Error handling

#### Key Features

1. **Dependency Management**
   - Automatic dependency resolution
   - Configuration order enforcement
   - Dependency validation
   - Skip handling for unmet dependencies

2. **Configuration Modes**
   - Full configuration deployment
   - Component-specific updates
   - Interactive configuration
   - Batch processing

3. **Error Handling**
   - Schema validation errors
   - Missing configuration detection
   - Dependency resolution failures
   - Component-specific errors

#### File Structure
- Configuration templates: `config/templates/`
- Schema definitions: `config/templates/schemas/`
- Component configurations:
  - realm.yml
  - security.yml
  - clients.yml
  - roles.yml
  - authentication.yml
  - events.yml
  - monitoring.yml
  - themes.yml
  - smtp.yml

### 6. Monitoring Setup (prometheus.py)

#### Overview
The `PrometheusManager` class handles the setup and configuration of monitoring infrastructure using Prometheus and Grafana. It provides comprehensive monitoring, alerting, and visualization capabilities.

#### Core Components

1. **Prometheus Setup**
   - Base Configuration:
     - Scrape interval: 15s
     - Evaluation interval: 15s
     - Retention time: 15d
   - Components:
     - Prometheus server
     - Node exporter
     - JMX exporter
     - Docker metrics integration

2. **Grafana Integration**
   - Dashboard management
   - Data source configuration
   - Alert notification channels
   - User authentication
   - SMTP configuration
   - Slack integration

#### Installation Process

1. **Prometheus Installation**
   - Package installation
   - Configuration deployment
   - Scrape config setup
   - Alert rules configuration
   - Docker metrics enablement
   - Service activation

2. **Grafana Setup**
   - Package installation
   - Configuration templating
   - Service initialization
   - Data source configuration
   - Dashboard import
   - Notification setup

#### Monitoring Features

1. **Metrics Collection**
   - System metrics
   - Keycloak metrics
   - Docker container stats
   - JVM metrics
   - Custom metrics

2. **Dashboard Configuration**
   - Keycloak overview
   - System overview
   - Performance metrics
   - Error tracking
   - User activity

3. **Alert Management**
   - Email notifications
   - Slack integration
   - Alert rules
   - Notification channels
   - Alert templating

#### Backup and Recovery

1. **Configuration Backup**
   - Prometheus config backup
   - Grafana settings backup
   - Dashboard preservation
   - Alert rules backup
   - Timestamp-based organization

2. **Recovery Process**
   - Configuration restoration
   - Service restart handling
   - Validation checks
   - Backup rotation
   - Error recovery

#### File Locations
- Prometheus config: `/etc/prometheus/`
- Grafana config: `/etc/grafana/`
- Backups: `/opt/fawz/keycloak/monitoring/backup/`
- Dashboards: `/opt/fawz/keycloak/monitoring/dashboards/`
- Docker config: `/etc/docker/daemon.json`

#### Integration Points
- Keycloak metrics endpoint
- Docker metrics API
- System metrics collection
- Alert notification systems
- Visualization platforms

### 7. Database Backup Management (database_backup.py)

#### Overview
The `DatabaseBackupStep` class manages automated database backup configuration for Keycloak's PostgreSQL database. It sets up scheduled backups through cron jobs and handles backup logging.

#### Core Components

1. **Backup Configuration**
   - Schedule management
   - Backup script setup
   - Logging configuration
   - Cron job integration
   - Permission handling

2. **Default Settings**
   - Default schedule: 0 2 * * * (2 AM daily)
   - Backup script location: `/opt/fawz/keycloak/scripts/db_backup.sh`
   - Log file: `/var/log/db_backup.log`
   - Cron configuration: `/etc/cron.d/db-backup`

#### Operational Features

1. **Scheduling**
   - Configurable backup schedule
   - Cron-based automation
   - Default nightly backups
   - Schedule override options
   - Continuous operation

2. **Logging**
   - Detailed backup logs
   - Error tracking
   - Success verification
   - Log rotation
   - Timestamp recording

3. **Security**
   - Secure file permissions
   - Root-level execution
   - Protected backup storage
   - Access control
   - Error isolation

#### Configuration Options

1. **Backup Settings**
   - Enable/disable backups
   - Custom schedule definition
   - Storage location
   - Retention policy
   - Log management

2. **Script Management**
   - Automated execution
   - Error handling
   - Status reporting
   - Resource cleanup
   - Process monitoring

#### Integration Points
- PostgreSQL database
- System scheduler
- Logging system
- Monitoring alerts
- Storage management

#### File Structure
- Backup script: `/opt/fawz/keycloak/scripts/db_backup.sh`
- Cron config: `/etc/cron.d/db-backup`
- Log file: `/var/log/db_backup.log`
- Backup storage: Configurable via database.backup.path

## Complete Deployment Flow Summary

### Sequence of Operations

1. **Installation (install.sh)**
   - System preparation
   - Repository setup
   - Module loading
   - Command setup

2. **Deployment Orchestration (deploy.py)**
   - Environment initialization
   - System checks
   - Component deployment
   - Status verification

3. **Component Setup**
   - System preparation
   - Docker infrastructure
   - SSL/TLS certificates
   - Keycloak deployment
   - Configuration management
   - Monitoring system
   - Backup procedures

### Key Integration Points

1. **Security Integration**
   - SSL/TLS management
   - Docker network isolation
   - Secure configuration storage
   - Backup encryption
   - Access control

2. **Monitoring Integration**
   - Prometheus metrics
   - Grafana dashboards
   - Alert management
   - Performance tracking
   - Health checks

3. **Data Management**
   - Database backups
   - Configuration backups
   - Certificate management
   - Log management
   - State persistence

### Best Practices

1. **Deployment**
   - Step-by-step validation
   - Dependency management
   - Error handling
   - Rollback capabilities
   - State verification

2. **Configuration**
   - Template-based setup
   - Schema validation
   - Version control
   - Environment separation
   - Documentation

3. **Maintenance**
   - Automated backups
   - Health monitoring
   - Alert systems
   - Log rotation
   - Update management










