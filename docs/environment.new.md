# Environment Variables Documentation

This document describes all environment variables used in the Keycloak Management System.

## Core Configuration

### Keycloak Server
- `KEYCLOAK_DOMAIN`: Domain name for Keycloak server
- `KEYCLOAK_PORT`: Port for Keycloak server (default: 8443)
- `KEYCLOAK_ADMIN`: Admin username for Keycloak (default: admin)
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password for Keycloak
- `KEYCLOAK_ADMIN_EMAIL`: Email address for admin account

### Database
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: keycloak)
- `DB_USER`: Database username (default: keycloak)
- `DB_PASSWORD`: Database password

### Docker
- `DOCKER_REGISTRY`: Docker registry to use (default: docker.io)
- `KEYCLOAK_VERSION`: Keycloak image version (default: latest)
- `POSTGRES_VERSION`: PostgreSQL image version (default: latest)

### SSL/TLS
- `SSL_CERT_PATH`: Path to SSL certificate file
- `SSL_KEY_PATH`: Path to SSL private key file
- `SSL_STAGING`: Use Let's Encrypt staging environment (default: false)
- `SSL_AUTO_RENEWAL`: Enable automatic certificate renewal (default: true)

## Component-Specific Variables

Each deployment step manages its own required variables:

### 1. System Preparation Step
Required packages:
- apt-transport-https
- ca-certificates
- curl
- gnupg

No specific environment variables required.

### 2. Docker Setup Step
Required variables:
- `DOCKER_REGISTRY`
- `FIREWALL_ALLOWED_PORTS` (for container ports)

Dependencies:
- Docker Engine
- Docker Compose

### 3. Certificate Management Step
Required variables:
- `KEYCLOAK_DOMAIN`
- `SSL_CERT_PATH`
- `SSL_KEY_PATH`
- `SSL_STAGING`
- `SSL_AUTO_RENEWAL`

Dependencies:
- certbot
- openssl

### 4. Keycloak Deployment Step
Required variables:
- `KEYCLOAK_PORT`
- `KEYCLOAK_ADMIN`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_ADMIN_EMAIL`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Dependencies:
- Docker network
- Docker volumes

### 5. Monitoring Setup Step
Required variables:
- `PROMETHEUS_SCRAPE_INTERVAL`
- `PROMETHEUS_EVAL_INTERVAL`
- `PROMETHEUS_RETENTION_TIME`
- `PROMETHEUS_DATA_DIR`
- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

Dependencies:
- prometheus
- grafana-server
- node_exporter

### 6. Backup Configuration Step
Required variables:
- `BACKUP_STORAGE_PATH`
- `BACKUP_TIME`
- `BACKUP_RETENTION_DAYS`
- `BACKUP_ENCRYPTION_KEY`

Dependencies:
- cron
- pg_dump

## Variable Management

Each component follows this process for managing variables:

1. **Variable Definition**
   ```python
   required_vars = [
       {
           'name': 'VARIABLE_NAME',
           'prompt': 'User-friendly prompt',
           'default': 'default_value'
       }
   ]
   ```

2. **Variable Resolution**
   - Check .env file first
   - Prompt user if missing
   - Save to .env for reuse
   - Validate before use

3. **Dependency Handling**
   - Check dependencies before use
   - Install if missing
   - Verify installation
   - Handle failures

## Usage Example

```python
# In a deployment step
from src.utils.environment import get_environment_manager

env_manager = get_environment_manager()
required_vars = [
    {
        'name': 'KEYCLOAK_PORT',
        'prompt': 'Enter Keycloak port',
        'default': '8443'
    }
]

# Get variables (will prompt if missing)
env_vars = env_manager.get_or_prompt_vars(required_vars)
```

## Best Practices

1. **Variable Definition**
   - Clear, descriptive names
   - Meaningful defaults where possible
   - Comprehensive prompts
   - Proper validation

2. **Security**
   - Secure storage of sensitive values
   - Encryption of credentials
   - Proper file permissions
   - Secure variable handling

3. **Maintenance**
   - Regular validation
   - Update documentation
   - Monitor for changes
   - Clean unused variables
