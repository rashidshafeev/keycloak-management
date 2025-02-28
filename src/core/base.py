import os
import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class BaseStep(ABC):
    """Base class for all deployment steps"""
    
    def __init__(self, name: str, can_cleanup: bool = False):
        """
        Initialize the deployment step
        
        Args:
            name: Step name
            can_cleanup: Whether the step can clean up after failure
        """
        self.name = name
        self.can_cleanup = can_cleanup
        self.logger = logging.getLogger(f"step.{name}")
        # Each step defines its own required variables
        self.required_vars = []
        
    def execute(self) -> bool:
        """Execute the deployment step"""
        self.logger.info(f"Starting step: {self.name}")
        try:
            # 1. Check and install dependencies
            if not self._check_dependencies():
                self.logger.info("Dependencies not met, attempting to install...")
                if not self._install_dependencies():
                    self.logger.error("Failed to install required dependencies")
                    return False
            
            # 2. Get environment variables
            try:
                env_vars = self._get_environment_variables()
            except Exception as e:
                self.logger.error(f"Failed to get environment variables: {str(e)}")
                return False
            
            # 3. Execute main operation
            try:
                if not self._deploy(env_vars):
                    self.logger.error(f"Deployment of {self.name} failed")
                    if self.can_cleanup:
                        self._cleanup()
                    return False
                
                self.logger.info(f"{self.name} completed successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Deployment failed: {str(e)}", exc_info=True)
                if self.can_cleanup:
                    self._cleanup()
                return False
                
        except Exception as e:
            self.logger.error(f"Step execution failed: {str(e)}", exc_info=True)
            return False
    
    def _get_environment_variables(self) -> Dict[str, str]:
        """Get or prompt for environment variables required by this step"""
        from ..utils.environment import get_environment_manager
        return get_environment_manager().get_or_prompt_vars(self.required_vars)
    
    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        self.logger.debug(f"Running command: {' '.join(command)}")
        try:
            return subprocess.run(command, check=check, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error output: {e.stderr}")
            if check:
                raise
            return e
    
    @abstractmethod
    def _check_dependencies(self) -> bool:
        """
        Check if required dependencies are installed
        
        Returns:
            True if all dependencies are installed, False otherwise
        """
        pass
    
    @abstractmethod
    def _install_dependencies(self) -> bool:
        """
        Install required dependencies
        
        Returns:
            True if installation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """
        Execute the main deployment operation
        
        Args:
            env_vars: Environment variables for this step
        
        Returns:
            True if deployment was successful, False otherwise
        """
        pass
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        # Default implementation does nothing
        # Steps should override this if they support cleanup
        pass