from typing import Dict, List
import logging

logger = logging.getLogger("step.system_preparation.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the system preparation step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'INSTALL_ROOT',
            'prompt': 'Enter installation root directory',
            'default': '/opt/keycloak'
        },
        {
            'name': 'LOG_DIR',
            'prompt': 'Enter log directory',
            'default': '/var/log/keycloak'
        },
        {
            'name': 'CONFIG_DIR',
            'prompt': 'Enter configuration directory',
            'default': '/etc/keycloak'
        },
        {
            'name': 'DATA_DIR',
            'prompt': 'Enter data directory',
            'default': '/var/lib/keycloak'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the system preparation step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Validation logic for system preparation environment variables
    required_vars = ['INSTALL_ROOT', 'LOG_DIR']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Additional validation could be added here
    
    return True