import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.wazuh_step.dependencies")

def check_wazuh_step_dependencies() -> bool:
    """
    Check if dependencies for the security monitoring with Wazuh step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    try:
        # Check if wazuh-manager is installed
        result = subprocess.run(
            ["systemctl", "status", "wazuh-manager"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Service doesn't need to be active, just installed
        if "Unit wazuh-manager.service could not be found" in result.stderr:
            logger.info("Wazuh Manager not installed")
            return False
            
        # Check for required directories
        wazuh_dir = os.path.exists("/var/ossec")
        if not wazuh_dir:
            logger.info("Wazuh directory not found")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def install_wazuh_step_dependencies() -> bool:
    """
    Install dependencies for the security monitoring with Wazuh step
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Add Wazuh repository
        subprocess.run([
            "curl", "-s", "https://packages.wazuh.com/key/GPG-KEY-WAZUH",
            "-o", "/usr/share/keyrings/wazuh.gpg"
        ], check=True)
        
        repo_command = "echo \"deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main\" > /etc/apt/sources.list.d/wazuh.list"
        subprocess.run(["bash", "-c", repo_command], check=True)
        
        # Update and install
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run([
            "apt-get", "install", "-y", 
            "wazuh-manager",
            "wazuh-indexer",
            "wazuh-dashboard"
        ], check=True)
        
        # Verify installation
        return check_wazuh_step_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False