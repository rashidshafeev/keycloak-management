"""
Monitoring configuration for Keycloak.
"""

from .base import KeycloakConfigStep
from .validation import ValidationError


class MonitoringConfigStep(KeycloakConfigStep):
    """Handles monitoring configuration for Keycloak.
    
    This step manages monitoring settings, including:
    - Metrics configuration
    - Health check endpoints
    - Monitoring integrations
    """
    
    def _validate_impl(self, config: dict) -> None:
        """Validate monitoring configuration."""
        metrics = config.get('metrics', {})
        if not isinstance(metrics, dict):
            raise ValidationError("'metrics' must be a dictionary", "metrics")
            
        health_check = config.get('health_check', {})
        if not isinstance(health_check, dict):
            raise ValidationError("'health_check' must be a dictionary", "health_check")
    
    def _execute_impl(self, config: dict) -> None:
        """Apply monitoring configuration."""
        # Enable metrics endpoint
        if config.get('metrics', {}).get('enabled', True):
            self.run_kcadm_command('update', 'realms/master', 
                                 '-s', 'metrics-enabled=true')
        
        # Configure health check endpoint
        if config.get('health_check', {}).get('enabled', True):
            self.run_kcadm_command('update', 'realms/master',
                                 '-s', 'health-check-enabled=true')
    
    def _rollback_impl(self) -> None:
        """Rollback monitoring configuration changes."""
        # Disable metrics and health check endpoints
        self.run_kcadm_command('update', 'realms/master',
                             '-s', 'metrics-enabled=false',
                             '-s', 'health-check-enabled=false')
