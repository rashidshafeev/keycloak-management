import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.grafana_step.dependencies")

def check_grafana_step_dependencies() -> bool:
    """
    Check if dependencies for the Grafana dashboard and visualization setup step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    try:
        # Check if apt-get is available
        apt_check = subprocess.run(
            ["apt-get", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        if apt_check.returncode != 0:
            logger.error("apt-get is not available")
            return False
            
        # Check if Grafana is installed
        grafana_check = subprocess.run(
            ["dpkg", "-l", "grafana"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        grafana_installed = grafana_check.returncode == 0
        
        # Check if curl is available (needed for API calls)
        curl_check = subprocess.run(
            ["curl", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        curl_available = curl_check.returncode == 0
        
        if not grafana_installed:
            logger.info("Grafana is not installed")
            return False
            
        if not curl_available:
            logger.info("curl is not installed (required for API calls)")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def install_grafana_step_dependencies() -> bool:
    """
    Install dependencies for the Grafana dashboard and visualization setup step
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Update package lists
        subprocess.run(["apt-get", "update"], check=True)
        
        # Add Grafana repository key
        subprocess.run([
            "apt-get", "install", "-y", "apt-transport-https", "software-properties-common", "curl"
        ], check=True)
        
        # Add Grafana repository
        subprocess.run([
            "curl", "https://packages.grafana.com/gpg.key", 
            "-o", "/etc/apt/trusted.gpg.d/grafana.gpg"
        ], check=True)
        
        # Add repository
        with open("/etc/apt/sources.list.d/grafana.list", "w") as f:
            f.write("deb https://packages.grafana.com/oss/deb stable main\n")
        
        # Update package lists again
        subprocess.run(["apt-get", "update"], check=True)
        
        # Install Grafana
        subprocess.run(["apt-get", "install", "-y", "grafana"], check=True)
        
        # Verify installation
        return check_grafana_step_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False
