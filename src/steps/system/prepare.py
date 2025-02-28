from ...core.base import BaseStep
import logging
import os
from typing import Dict, List

# Import step-specific modules
from .dependencies import check_system_dependencies, install_system_dependencies
from .environment import get_required_variables, validate_variables

class SystemPreparationStep(BaseStep):
    """Step for preparing the system environment"""
    
    def __init__(self):
        super().__init__("system_preparation", can_cleanup=False)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required packages are installed"""
        return check_system_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required packages"""
        return install_system_dependencies()
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Configure system directories and permissions"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Create installation root directory
            install_root = env_vars.get('INSTALL_ROOT', '/opt/keycloak')
            os.makedirs(install_root, exist_ok=True)
            self.logger.info(f"Created installation directory: {install_root}")
            
            # Create log directory
            log_dir = env_vars.get('LOG_DIR', '/var/log/keycloak')
            os.makedirs(log_dir, exist_ok=True)
            self.logger.info(f"Created log directory: {log_dir}")
            
            # Create config directory
            config_dir = env_vars.get('CONFIG_DIR', '/etc/keycloak')
            os.makedirs(config_dir, exist_ok=True)
            self.logger.info(f"Created configuration directory: {config_dir}")
            
            # Create data directory if specified
            if 'DATA_DIR' in env_vars:
                data_dir = env_vars['DATA_DIR']
                os.makedirs(data_dir, exist_ok=True)
                self.logger.info(f"Created data directory: {data_dir}")
            
            # Set proper permissions
            # TODO: In a real implementation, use proper user/group instead of 0755
            for directory in [install_root, log_dir, config_dir]:
                os.chmod(directory, 0o755)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure system directories: {str(e)}")
            return False