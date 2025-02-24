import os
import logging
import socket
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """Utility for managing environment variables"""
    
    def __init__(self):
        self.env_file = Path('.env')

    def get_or_prompt_vars(self, required_vars: List[Dict]) -> Dict[str, str]:
        """
        Get required variables from environment or prompt for them
        
        Args:
            required_vars: List of dictionaries containing variable configurations
                Example: [
                    {
                        'name': 'KEYCLOAK_PORT',
                        'prompt': 'Enter Keycloak port',
                        'default': '8443'
                    },
                    {
                        'name': 'KEYCLOAK_ADMIN_EMAIL',
                        'prompt': 'Enter admin email',
                        'default': f'admin@{socket.getfqdn()}'
                    }
                ]
        
        Returns:
            Dictionary with variable names and their values
        """
        env_vars = {}
        
        # Load existing environment if available
        if self.env_file.exists():
            load_dotenv()
        
        # Check each required variable
        for var_config in required_vars:
            var_name = var_config['name']
            value = os.getenv(var_name)
            
            if not value:
                # Variable not found in environment, prompt for it
                default = var_config.get('default')
                prompt = f"{var_config['prompt']}"
                if default:
                    prompt += f" [{default}]"
                prompt += ": "
                
                value = input(prompt)
                if not value and default:
                    value = default
                
                # Save to environment file for future use
                self._append_to_env_file(var_name, value)
            
            env_vars[var_name] = value
        
        return env_vars

    def _append_to_env_file(self, key: str, value: str) -> None:
        """Append a new variable to the .env file"""
        try:
            mode = 'a' if self.env_file.exists() else 'w'
            with open(self.env_file, mode) as f:
                f.write(f"{key}={value}\n")
            
            # Secure the .env file
            self.env_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save variable to environment file: {str(e)}")
            raise

def get_environment_manager() -> EnvironmentManager:
    """Get or create an EnvironmentManager instance"""
    if not hasattr(get_environment_manager, 'instance'):
        get_environment_manager.instance = EnvironmentManager()
    return get_environment_manager.instance
