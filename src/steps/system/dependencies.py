import os
import subprocess
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger("step.system_preparation.dependencies")

def check_system_dependencies() -> bool:
    """
    Check if all required system packages are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    required_packages = ['apt-transport-https', 'ca-certificates', 'curl', 'gnupg']
    
    # Check if we're on Debian-based system
    if not os.path.exists('/etc/debian_version'):
        logger.warning("Non-Debian system detected. Package installation may not work correctly.")
        # For non-Debian systems, just check for curl as a basic requirement
        try:
            result = subprocess.run(['curl', '--version'], 
                                   check=False, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    # Use dpkg to check for installed packages
    try:
        for package in required_packages:
            result = subprocess.run(['dpkg', '-l', package], 
                                   check=False, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            if result.returncode != 0:
                logger.info(f"Package {package} is not installed")
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def install_system_dependencies() -> bool:
    """
    Install required system packages
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    # Only works on Debian-based systems
    if not os.path.exists('/etc/debian_version'):
        logger.error("Cannot install packages on non-Debian system")
        return False
    
    try:
        # Update package lists
        subprocess.run(['apt-get', 'update'], check=True)
        
        # Install required packages
        packages = ['apt-transport-https', 'ca-certificates', 'curl', 'gnupg']
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        return check_system_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        logger.error(f"Command output: {e.stderr if hasattr(e, 'stderr') else 'No output'}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False