from typing import Dict, List
import logging

logger = logging.getLogger("step.wazuh_step.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the security monitoring with Wazuh step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'WAZUH_MANAGER_PORT',
            'prompt': 'Wazuh manager port',
            'default': '1514'
        },
        {
            'name': 'WAZUH_PROTOCOL',
            'prompt': 'Wazuh protocol (tcp/udp)',
            'default': 'tcp'
        },
        {
            'name': 'WAZUH_NOTIFICATION_EMAIL',
            'prompt': 'Email address for Wazuh alerts',
            'default': 'admin@example.com'
        },
        {
            'name': 'WAZUH_ALERT_LEVEL',
            'prompt': 'Minimum level for alerts (3-15)',
            'default': '7'
        },
        {
            'name': 'WAZUH_BACKUP_DIR',
            'prompt': 'Wazuh backup directory',
            'default': '/opt/fawz/keycloak/wazuh/backup'
        },
        {
            'name': 'WAZUH_CONFIG_DIR',
            'prompt': 'Wazuh configuration directory',
            'default': '/opt/fawz/keycloak/wazuh/config'
        },
        {
            'name': 'WAZUH_MAX_BACKUPS',
            'prompt': 'Maximum number of Wazuh backups to keep',
            'default': '5'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the security monitoring with Wazuh step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['WAZUH_MANAGER_PORT', 'WAZUH_PROTOCOL', 'WAZUH_NOTIFICATION_EMAIL']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate port number
    try:
        port = int(env_vars.get('WAZUH_MANAGER_PORT', '1514'))
        if port < 1 or port > 65535:
            logger.error(f"Invalid port number: {port}")
            return False
    except ValueError:
        logger.error(f"Port must be a number: {env_vars.get('WAZUH_MANAGER_PORT')}")
        return False
    
    # Validate protocol
    protocol = env_vars.get('WAZUH_PROTOCOL', 'tcp').lower()
    if protocol not in ['tcp', 'udp']:
        logger.error(f"Protocol must be 'tcp' or 'udp': {protocol}")
        return False
    
    # Validate alert level
    try:
        level = int(env_vars.get('WAZUH_ALERT_LEVEL', '7'))
        if level < 1 or level > 15:
            logger.error(f"Alert level must be between 1 and 15: {level}")
            return False
    except ValueError:
        logger.error(f"Alert level must be a number: {env_vars.get('WAZUH_ALERT_LEVEL')}")
        return False
    
    return True