import logging
from typing import List, Dict, Any, Optional
from .environment import EnvironmentChecker
from .dependencies import DependencyChecker

class BaseStep:
    """Base class for all deployment steps"""
    
    def __init__(self, name: str, can_skip: bool = False, can_cleanup: bool = True):
        """
        Initialize the base step
        
        Args:
            name: Name of the step
            can_skip: Whether the step can be skipped
            can_cleanup: Whether the step can be cleaned up
        """
        self.name = name
        self.can_skip = can_skip
        self.can_cleanup = can_cleanup
        self.logger = logging.getLogger(f"step.{name}")
        self.env_checker = None
        self.dep_checker = None
    
    def setup_environment_checker(self, required_vars: List[str] = None, optional_vars: List[str] = None) -> None:
        """Set up the environment checker"""
        self.env_checker = EnvironmentChecker(required_vars, optional_vars)
    
    def setup_dependency_checker(self, required_packages: List[str] = None, required_commands: List[str] = None) -> None:
        """Set up the dependency checker"""
        self.dep_checker = DependencyChecker(required_packages, required_commands)
    
    def check_environment(self) -> bool:
        """Check if all required environment variables are present"""
        if not self.env_checker:
            return True
        return self.env_checker.check_and_process_environment()
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        if not self.dep_checker:
            return True
        return self.dep_checker.check_and_install_dependencies()
    
    def check_completed(self) -> bool:
        """Check if the step has already been completed"""
        return False
    
    def execute(self) -> bool:
        """Execute the step"""
        # Check environment and dependencies first
        if not self.check_environment():
            self.logger.error(f"Step {self.name} failed: environment check failed")
            return False
            
        if not self.check_dependencies():
            self.logger.error(f"Step {self.name} failed: dependency check failed")
            return False
            
        # Implement step-specific logic in subclasses
        return True
    
    def cleanup(self) -> bool:
        """Clean up after the step"""
        return True