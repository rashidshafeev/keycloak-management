import os
import subprocess
import logging
import platform
from typing import List, Dict, Tuple, Optional, Set

logger = logging.getLogger(__name__)

class DependencyChecker:
    """Base class for dependency checking and installation"""
    
    def __init__(self, required_packages: List[str] = None, required_commands: List[str] = None):
        """
        Initialize the dependency checker
        
        Args:
            required_packages: List of required system packages
            required_commands: List of required commands
        """
        self.required_packages = required_packages or []
        self.required_commands = required_commands or []
        self.is_debian = self._is_debian_based()
        self.is_container = self._is_in_container()
    
    def _is_debian_based(self) -> bool:
        """Check if the system is Debian-based"""
        return os.path.exists('/etc/debian_version')

    def _is_in_container(self) -> bool:
        """Check if running inside a container"""
        return os.path.exists('/.dockerenv') or any('docker' in line for line in open('/proc/1/cgroup', 'r').readlines())

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        try:
            return subprocess.run(command, check=check, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output: {e.stderr}")
            if check:
                raise
    
    def check_command(self, command: str) -> bool:
        """Check if a command is available"""
        try:
            self._run_command(["which", command], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_package(self, package: str) -> bool:
        """Check if a package is installed"""
        if not self.is_debian:
            logger.warning("Non-Debian system detected. Package check may not work.")
            return self.check_command(package)
            
        try:
            result = self._run_command(["dpkg", "-l", package], check=False)
            return "ii" in result.stdout
        except Exception:
            return False
    
    def install_package(self, package: str) -> bool:
        """Install a package"""
        if not self.is_debian:
            logger.warning("Non-Debian system detected. Package installation may not work.")
            return False
            
        try:
            self._run_command(["apt-get", "update"])
            self._run_command(["apt-get", "install", "-y", package])
            return True
        except Exception as e:
            logger.error(f"Failed to install package {package}: {str(e)}")
            return False
    
    def check_dependencies(self) -> List[str]:
        """Check all dependencies and return list of missing ones"""
        missing = []
        
        # Check required commands
        for command in self.required_commands:
            if not self.check_command(command):
                missing.append(f"Command not found: {command}")
        
        # Check required packages
        for package in self.required_packages:
            if not self.check_package(package):
                missing.append(f"Package not installed: {package}")
        
        return missing
    
    def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        success = True
        
        # Install required packages
        for package in self.required_packages:
            if not self.check_package(package):
                logger.info(f"Installing package: {package}")
                if not self.install_package(package):
                    success = False
        
        return success
    
    def check_and_install_dependencies(self) -> bool:
        """Check and install dependencies if needed"""
        missing = self.check_dependencies()
        if not missing:
            logger.info("All dependencies are satisfied")
            return True
            
        logger.info(f"Missing dependencies: {', '.join(missing)}")
        return self.install_dependencies()