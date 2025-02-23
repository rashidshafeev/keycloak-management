import os
import logging
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
from .dependencies import DependencyManager

logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """Handle environment setup and configuration"""
    
    def __init__(self):
        self.dep_manager = DependencyManager()
        self.env_file = Path('.env')
        self.required_vars = [
            'KEYCLOAK_DOMAIN',
            'KEYCLOAK_ADMIN_EMAIL',
            'KEYCLOAK_ADMIN_PASSWORD',
            'DB_PASSWORD'
        ]

    def setup(self) -> bool:
        """Set up environment configuration"""
        try:
            # Check Docker availability
            if not self.dep_manager.check_docker()[0]:
                logger.error("Docker is not available")
                return False

            # Load existing environment if available
            if self.env_file.exists():
                env_vars = load_environment()
                if self._validate_environment(env_vars):
                    logger.info("Environment already configured")
                    return True

            # Create new environment configuration
            env_vars = self._create_environment()
            if not env_vars:
                return False

            # Save environment configuration
            self._save_environment(env_vars)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set up environment: {str(e)}")
            return False

    def _validate_environment(self, env_vars: Dict[str, str]) -> bool:
        """Validate that all required environment variables are present"""
        missing_vars = [var for var in self.required_vars if var not in env_vars]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        return True

    def _create_environment(self) -> Optional[Dict[str, str]]:
        """Create new environment configuration"""
        try:
            # Here you would implement logic to gather environment variables
            # This could involve prompting the user, generating values, etc.
            env_vars = {
                'KEYCLOAK_DOMAIN': 'localhost',
                'KEYCLOAK_ADMIN_EMAIL': 'admin@example.com',
                'KEYCLOAK_ADMIN_PASSWORD': 'admin123',
                'DB_PASSWORD': 'db123'
            }
            
            return env_vars
        except Exception as e:
            logger.error(f"Failed to create environment configuration: {str(e)}")
            return None

    def _save_environment(self, env_vars: Dict[str, str]) -> None:
        """Save environment configuration to file"""
        try:
            with open(self.env_file, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            logger.error(f"Failed to save environment configuration: {str(e)}")
            raise

def load_environment() -> Dict[str, str]:
    """Load environment variables from .env file"""
    if not load_dotenv():
        raise Exception("Failed to load environment configuration")
    
    env_vars = {}
    for key in os.environ:
        env_vars[key] = os.environ[key]
    
    return env_vars
