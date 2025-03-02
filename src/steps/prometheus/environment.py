from typing import Dict, List
import logging

logger = logging.getLogger("step.prometheus_step.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the Prometheus monitoring system setup step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'PROMETHEUS_SCRAPE_INTERVAL',
            'prompt': 'Prometheus scrape interval',
            'default': '15s'
        },
        {
            'name': 'PROMETHEUS_EVAL_INTERVAL',
            'prompt': 'Prometheus evaluation interval',
            'default': '15s'
        },
        {
            'name': 'PROMETHEUS_RETENTION_TIME',
            'prompt': 'Prometheus data retention time',
            'default': '15d'
        },
        {
            'name': 'PROMETHEUS_BACKUP_DIR',
            'prompt': 'Prometheus backup directory',
            'default': '/opt/fawz/keycloak/monitoring/backup/prometheus'
        },
        {
            'name': 'DOCKER_METRICS_PORT',
            'prompt': 'Docker metrics port',
            'default': '9323'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the Prometheus monitoring system setup step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['PROMETHEUS_SCRAPE_INTERVAL', 'PROMETHEUS_EVAL_INTERVAL', 'PROMETHEUS_RETENTION_TIME']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate time formats (should end with s, m, h, d)
    time_vars = ['PROMETHEUS_SCRAPE_INTERVAL', 'PROMETHEUS_EVAL_INTERVAL', 'PROMETHEUS_RETENTION_TIME']
    for var in time_vars:
        value = env_vars.get(var, '')
        if not (value and value[-1] in 'smhd' and value[:-1].isdigit()):
            logger.error(f"Variable {var} must be a number followed by s, m, h, or d. Got: {value}")
            return False
    
    return True
