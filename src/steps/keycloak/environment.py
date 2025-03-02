from typing import Dict, List
import logging

logger = logging.getLogger("step.keycloak_deployment.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the Keycloak server deployment and configuration step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        # Database Configuration
        {
            'name': 'DB_NAME',
            'prompt': 'Keycloak database name',
            'default': 'keycloak'
        },
        {
            'name': 'DB_USER',
            'prompt': 'Keycloak database user',
            'default': 'keycloak'
        },
        {
            'name': 'DB_PASSWORD',
            'prompt': 'Keycloak database password',
            'default': ''
        },
        
        # Keycloak Admin Configuration
        {
            'name': 'KEYCLOAK_ADMIN',
            'prompt': 'Keycloak admin username',
            'default': 'admin'
        },
        {
            'name': 'KEYCLOAK_ADMIN_PASSWORD',
            'prompt': 'Keycloak admin password',
            'default': ''
        },
        
        # Network Configuration
        {
            'name': 'KEYCLOAK_FRONTEND_URL',
            'prompt': 'Keycloak frontend URL (e.g., https://auth.example.com/auth)',
            'default': 'http://localhost:8080/auth'
        },
        {
            'name': 'KEYCLOAK_HTTP_PORT',
            'prompt': 'Keycloak HTTP port',
            'default': '8080'
        },
        {
            'name': 'KEYCLOAK_HTTPS_PORT',
            'prompt': 'Keycloak HTTPS port',
            'default': '8443'
        },
        
        # Container Configuration
        {
            'name': 'KEYCLOAK_IMAGE',
            'prompt': 'Keycloak Docker image',
            'default': 'quay.io/keycloak/keycloak:latest'
        },
        {
            'name': 'POSTGRES_IMAGE',
            'prompt': 'PostgreSQL Docker image',
            'default': 'postgres:15'
        },
        
        # Resource Configuration
        {
            'name': 'KEYCLOAK_MEM_LIMIT',
            'prompt': 'Keycloak memory limit',
            'default': '2g'
        },
        {
            'name': 'KEYCLOAK_MEM_RESERVATION',
            'prompt': 'Keycloak memory reservation',
            'default': '1g'
        },
        {
            'name': 'POSTGRES_MEM_LIMIT',
            'prompt': 'PostgreSQL memory limit',
            'default': '1g'
        },
        {
            'name': 'POSTGRES_MEM_RESERVATION',
            'prompt': 'PostgreSQL memory reservation',
            'default': '512m'
        },
        
        # Event Configuration
        {
            'name': 'EVENT_WEBHOOK_SECRET',
            'prompt': 'Webhook secret for event listeners',
            'default': ''
        },
        {
            'name': 'EVENT_STORAGE_EXPIRATION',
            'prompt': 'Event storage expiration in seconds (30 days = 2592000)',
            'default': '2592000'
        },
        
        # Volume Configuration
        {
            'name': 'KEYCLOAK_DATA_DIR',
            'prompt': 'Local path for Keycloak data',
            'default': '/opt/fawz/keycloak/data'
        },
        {
            'name': 'POSTGRES_DATA_DIR',
            'prompt': 'Local path for PostgreSQL data',
            'default': '/opt/fawz/keycloak/postgres-data'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the Keycloak server deployment and configuration step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['DB_PASSWORD', 'KEYCLOAK_ADMIN_PASSWORD']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate numeric values
    try:
        http_port = int(env_vars.get('KEYCLOAK_HTTP_PORT', '8080'))
        if http_port < 1 or http_port > 65535:
            logger.error(f"HTTP port must be between 1 and 65535: {http_port}")
            return False
            
        https_port = int(env_vars.get('KEYCLOAK_HTTPS_PORT', '8443'))
        if https_port < 1 or https_port > 65535:
            logger.error(f"HTTPS port must be between 1 and 65535: {https_port}")
            return False
    except ValueError:
        logger.error("Port must be a valid number")
        return False
    
    # Validate frontend URL format
    frontend_url = env_vars.get('KEYCLOAK_FRONTEND_URL', '')
    if not (frontend_url.startswith('http://') or frontend_url.startswith('https://')):
        logger.error(f"Frontend URL must start with http:// or https://: {frontend_url}")
        return False
    
    # Validate event storage expiration
    try:
        expiration = int(env_vars.get('EVENT_STORAGE_EXPIRATION', '2592000'))
        if expiration < 0:
            logger.error(f"Event storage expiration must be a positive number: {expiration}")
            return False
    except ValueError:
        logger.error("Event storage expiration must be a number")
        return False
    
    return True
