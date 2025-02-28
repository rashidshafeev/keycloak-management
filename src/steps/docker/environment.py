from typing import Dict, List
import logging
import ipaddress

logger = logging.getLogger("step.docker_setup.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the Docker setup step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'DOCKER_NETWORK',
            'prompt': 'Enter Docker network name',
            'default': 'keycloak-network'
        },
        {
            'name': 'DOCKER_NETWORK_SUBNET',
            'prompt': 'Enter Docker network subnet',
            'default': '172.20.0.0/16'
        },
        {
            'name': 'DOCKER_VOLUMES_PATH',
            'prompt': 'Enter Docker volumes path',
            'default': '/var/lib/docker/volumes'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the Docker setup step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['DOCKER_NETWORK', 'DOCKER_NETWORK_SUBNET']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate subnet format
    subnet = env_vars.get('DOCKER_NETWORK_SUBNET')
    if subnet:
        try:
            ipaddress.ip_network(subnet)
        except ValueError as e:
            logger.error(f"Invalid network subnet format: {subnet}, error: {str(e)}")
            return False
    
    return True