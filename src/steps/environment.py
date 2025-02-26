import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentChecker:
    """Base class for environment variable checking and processing"""
    
    def __init__(self, required_vars: List[str] = None, optional_vars: List[str] = None):
        """
        Initialize the environment checker
        
        Args:
            required_vars: List of required environment variables
            optional_vars: List of optional environment variables
        """
        self.required_vars = required_vars or []
        self.optional_vars = optional_vars or []
        self.env_file = Path('.env')
        self.env_vars = {}
    
    def load_environment(self) -> Dict[str, str]:
        """Load environment variables from .env file"""
        if not self.env_file.exists():
            logger.warning(f"Environment file {self.env_file} not found")
            return {}
            
        if not load_dotenv(self.env_file):
            logger.warning(f"Failed to load environment from {self.env_file}")
            
        env_vars = {}
        for key in os.environ:
            env_vars[key] = os.environ[key]
        
        self.env_vars = env_vars
        return env_vars
    
    def check_required_vars(self) -> List[str]:
        """Check if all required environment variables are present"""
        if not self.env_vars:
            self.load_environment()
            
        missing_vars = [var for var in self.required_vars if var not in self.env_vars]
        return missing_vars
    
    def get_var(self, var_name: str, default: str = None) -> Optional[str]:
        """Get an environment variable value"""
        if not self.env_vars:
            self.load_environment()
            
        return self.env_vars.get(var_name, default)
    
    def set_var(self, var_name: str, value: str) -> None:
        """Set an environment variable value"""
        self.env_vars[var_name] = value
        os.environ[var_name] = value
    
    def save_environment(self) -> bool:
        """Save environment variables to .env file"""
        try:
            with open(self.env_file, 'w') as f:
                for key, value in self.env_vars.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to save environment: {str(e)}")
            return False
    
    def prompt_for_missing_vars(self) -> bool:
        """Prompt for missing environment variables"""
        missing_vars = self.check_required_vars()
        if not missing_vars:
            return True
            
        logger.info(f"Missing required environment variables: {', '.join(missing_vars)}")
        # Implementation would depend on the UI framework used
        # For now, just return False
        return False
    
    def check_and_process_environment(self) -> bool:
        """Check and process environment variables"""
        missing_vars = self.check_required_vars()
        if missing_vars:
            return self.prompt_for_missing_vars()
        return True