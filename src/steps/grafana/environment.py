from typing import Dict, List
import logging

logger = logging.getLogger("step.grafana_step.environment")

def get_required_variables() -> List[Dict]:
    """
    Define environment variables required by the Grafana dashboard and visualization setup step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    """
    return [
        {
            'name': 'GRAFANA_ADMIN_USER',
            'prompt': 'Grafana admin username',
            'default': 'admin'
        },
        {
            'name': 'GRAFANA_ADMIN_PASSWORD',
            'prompt': 'Grafana admin password',
            'default': 'admin'
        },
        {
            'name': 'GRAFANA_BACKUP_DIR',
            'prompt': 'Grafana backup directory',
            'default': '/opt/fawz/keycloak/monitoring/backup/grafana'
        },
        {
            'name': 'GRAFANA_DASHBOARD_DIR',
            'prompt': 'Grafana dashboards directory',
            'default': '/opt/fawz/keycloak/monitoring/dashboards'
        },
        {
            'name': 'GRAFANA_SMTP_HOST',
            'prompt': 'SMTP server for Grafana alerts (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_SMTP_USER',
            'prompt': 'SMTP username (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_SMTP_PASSWORD',
            'prompt': 'SMTP password (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_SMTP_FROM',
            'prompt': 'Email address for alerts (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_ALERT_EMAIL',
            'prompt': 'Email to receive alerts (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_SLACK_WEBHOOK_URL',
            'prompt': 'Slack webhook URL for alerts (optional)',
            'default': ''
        },
        {
            'name': 'GRAFANA_SLACK_CHANNEL',
            'prompt': 'Slack channel for alerts (optional)',
            'default': '#alerts'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate environment variables for the Grafana dashboard and visualization setup step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    """
    # Check if required variables are present
    required_vars = ['GRAFANA_ADMIN_USER', 'GRAFANA_ADMIN_PASSWORD']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {var} is missing or empty")
            return False
    
    # Validate email settings consistency
    if (env_vars.get('GRAFANA_SMTP_HOST') or 
        env_vars.get('GRAFANA_ALERT_EMAIL') or 
        env_vars.get('GRAFANA_SMTP_FROM')):
        
        # If any email setting is provided, check that the essential ones are there
        if not env_vars.get('GRAFANA_SMTP_HOST'):
            logger.error("GRAFANA_SMTP_HOST is required when configuring email alerts")
            return False
            
        if not env_vars.get('GRAFANA_ALERT_EMAIL'):
            logger.error("GRAFANA_ALERT_EMAIL is required when configuring email alerts")
            return False
            
        if not env_vars.get('GRAFANA_SMTP_FROM'):
            logger.error("GRAFANA_SMTP_FROM is required when configuring email alerts")
            return False
    
    return True
