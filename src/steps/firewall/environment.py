from typing import Dict, List
import logging
import ipaddress

logger = logging.getLogger("step.firewallstep.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the firewall configuration step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'FIREWALL_RULES_DIR',
            'prompt': 'Enter firewall rules directory',
            'default': '/etc/keycloak/firewall/rules'
        },
        {
            'name': 'FIREWALL_BACKUP_DIR',
            'prompt': 'Enter firewall backup directory',
            'default': '/etc/keycloak/firewall/backup'
        },
        {
            'name': 'FIREWALL_MAX_BACKUPS',
            'prompt': 'Enter maximum number of firewall backups to keep',
            'default': '5'
        },
        {
            'name': 'KEYCLOAK_PORT',
            'prompt': 'Enter Keycloak HTTPS port',
            'default': '8443'
        },
        {
            'name': 'KEYCLOAK_HTTP_PORT',
            'prompt': 'Enter Keycloak HTTP port',
            'default': '8080'
        },
        {
            'name': 'KEYCLOAK_MANAGEMENT_PORT', 
            'prompt': 'Enter Keycloak management port',
            'default': '9990'
        },
        {
            'name': 'KEYCLOAK_AJP_PORT',
            'prompt': 'Enter Keycloak AJP port',
            'default': '8009'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the firewall configuration step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['FIREWALL_RULES_DIR', 'FIREWALL_BACKUP_DIR']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate port numbers
    port_vars = ['KEYCLOAK_PORT', 'KEYCLOAK_HTTP_PORT', 'KEYCLOAK_MANAGEMENT_PORT', 'KEYCLOAK_AJP_PORT']
    for var in port_vars:
        if var in env_vars:
            try:
                port = int(env_vars[var])
                if port < 1 or port > 65535:
                    logger.error(f"Invalid port number for {var}: {port}")
                    return False
            except ValueError:
                logger.error(f"Invalid port format for {var}: {env_vars[var]}")
                return False
    
    # Validate backup count
    if 'FIREWALL_MAX_BACKUPS' in env_vars:
        try:
            backups = int(env_vars['FIREWALL_MAX_BACKUPS'])
            if backups < 1:
                logger.error(f"Invalid backup count: {backups}")
                return False
        except ValueError:
            logger.error(f"Invalid backup count format: {env_vars['FIREWALL_MAX_BACKUPS']}")
            return False
    
    return True
