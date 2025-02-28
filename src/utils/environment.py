import os
import logging
import socket
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """Utility for managing environment variables"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        Initialize environment manager
        
        Args:
            env_file_path: Path to .env file, defaults to current directory
        """
        self.env_file = Path(env_file_path) if env_file_path else Path('.env')

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
            load_dotenv(dotenv_path=self.env_file)
        
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
        """
        Append a new variable to the .env file or update existing value
        
        Args:
            key: Environment variable name
            value: Environment variable value
        """
        try:
            # Create parent directories if needed
            self.env_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine if we need to create new file or update existing
            mode = 'a' if self.env_file.exists() else 'w'
            
            if mode == 'a' and self.env_file.exists():
                # Use dotenv's set_key for existing file to avoid duplication
                set_key(str(self.env_file), key, value)
            else:
                # Create new file
                with open(self.env_file, mode) as f:
                    f.write(f"{key}={value}\n")
            
            # Secure the .env file
            self.env_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save variable to environment file: {str(e)}")
            raise

def get_environment_manager(env_file_path: Optional[str] = None) -> EnvironmentManager:
    """
    Get or create an EnvironmentManager instance
    
    Args:
        env_file_path: Optional path to .env file
        
    Returns:
        EnvironmentManager instance
    """
    if not hasattr(get_environment_manager, 'instance') or \
       (env_file_path and get_environment_manager.instance.env_file != Path(env_file_path)):
        get_environment_manager.instance = EnvironmentManager(env_file_path)
    return get_environment_manager.instance
