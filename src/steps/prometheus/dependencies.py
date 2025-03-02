import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.prometheus_step.dependencies")

def check_prometheus_step_dependencies() -> bool:
    """
    Check if dependencies for the Prometheus monitoring system setup step are installed
    
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
            
        # Check if prometheus is installed
        prometheus_check = subprocess.run(
            ["dpkg", "-l", "prometheus"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        prometheus_installed = prometheus_check.returncode == 0
        
        # Check if node_exporter is installed
        node_exporter_check = subprocess.run(
            ["dpkg", "-l", "prometheus-node-exporter"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        node_exporter_installed = node_exporter_check.returncode == 0
        
        # Check if jmx_exporter is installed
        jmx_exporter_check = subprocess.run(
            ["dpkg", "-l", "prometheus-jmx-exporter"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        jmx_exporter_installed = jmx_exporter_check.returncode == 0
        
        if not prometheus_installed:
            logger.info("Prometheus is not installed")
            return False
            
        if not node_exporter_installed:
            logger.info("Prometheus Node Exporter is not installed")
            return False
            
        if not jmx_exporter_installed:
            logger.info("Prometheus JMX Exporter is not installed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def install_prometheus_step_dependencies() -> bool:
    """
    Install dependencies for the Prometheus monitoring system setup step
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Update package lists
        subprocess.run(["apt-get", "update"], check=True)
        
        # Install required packages
        subprocess.run([
            "apt-get", "install", "-y",
            "prometheus",
            "prometheus-node-exporter",
            "prometheus-jmx-exporter"
        ], check=True)
        
        # Verify installation
        return check_prometheus_step_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False
