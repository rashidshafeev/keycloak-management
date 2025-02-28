from typing import Dict, List
import logging
import os
from pathlib import Path

logger = logging.getLogger("step.certificatestep.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the certificate management step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'SSL_DOMAINS',
            'prompt': 'Enter comma-separated list of domains for SSL certificate',
            'default': None  # Must be provided
        },
        {
            'name': 'SSL_EMAIL',
            'prompt': 'Enter email address for SSL certificate notifications',
            'default': None  # Must be provided
        },
        {
            'name': 'SSL_STAGING',
            'prompt': 'Use Let\'s Encrypt staging environment (true/false)',
            'default': 'true'
        },
        {
            'name': 'SSL_AUTO_RENEWAL',
            'prompt': 'Enable automatic certificate renewal (true/false)',
            'default': 'true'
        },
        {
            'name': 'SSL_MIN_DAYS_VALID',
            'prompt': 'Minimum days certificate should be valid',
            'default': '30'
        },
        {
            'name': 'SSL_MAX_BACKUPS',
            'prompt': 'Maximum number of certificate backups to keep',
            'default': '5'
        },
        {
            'name': 'SSL_CERT_DIR',
            'prompt': 'Directory for SSL certificates',
            'default': '/etc/letsencrypt/live'
        },
        {
            'name': 'SSL_BACKUP_DIR',
            'prompt': 'Directory for certificate backups',
            'default': '/opt/keycloak/certs/backup'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the certificate management step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check required variables
    required_vars = ['SSL_DOMAINS', 'SSL_EMAIL']
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate email format
    email = env_vars.get('SSL_EMAIL', '')
    if not '@' in email or not '.' in email:
        logger.error(f"Invalid email format: {email}")
        return False
    
    # Validate domains
    domains = env_vars.get('SSL_DOMAINS', '').split(',')
    if not domains:
        logger.error("No domains specified")
        return False
    
    for domain in domains:
        domain = domain.strip()
        if not domain:
            logger.error("Empty domain found in list")
            return False
        if not '.' in domain:
            logger.error(f"Invalid domain format: {domain}")
            return False
    
    # Validate numeric values
    try:
        min_days = int(env_vars.get('SSL_MIN_DAYS_VALID', '30'))
        if min_days < 1:
            logger.error(f"SSL_MIN_DAYS_VALID must be positive: {min_days}")
            return False
            
        max_backups = int(env_vars.get('SSL_MAX_BACKUPS', '5'))
        if max_backups < 1:
            logger.error(f"SSL_MAX_BACKUPS must be positive: {max_backups}")
            return False
    except ValueError as e:
        logger.error(f"Invalid numeric value: {str(e)}")
        return False
    
    # Validate boolean values
    for bool_var in ['SSL_STAGING', 'SSL_AUTO_RENEWAL']:
        value = env_vars.get(bool_var, '').lower()
        if value not in ['true', 'false']:
            logger.error(f"{bool_var} must be 'true' or 'false': {value}")
            return False
    
    # Validate directories
    cert_dir = Path(env_vars.get('SSL_CERT_DIR', '/etc/letsencrypt/live'))
    backup_dir = Path(env_vars.get('SSL_BACKUP_DIR', '/opt/keycloak/certs/backup'))
    
    # Create directories if they don't exist
    try:
        cert_dir.parent.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create certificate directories: {str(e)}")
        return False
    
    return True
