from typing import Dict, List
import logging

logger = logging.getLogger("step.wazuhstep.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the Wazuh Security Monitoring step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'EXAMPLE_VAR',
            'prompt': 'Example variable',
            'default': 'default-value'
        },
        # Add more required variables here
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the Wazuh Security Monitoring step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['EXAMPLE_VAR']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Add additional validation if needed
    
    return True
