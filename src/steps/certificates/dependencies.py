import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.certificatestep.dependencies")

def check_certificatestep_dependencies() -> bool:
    """
    Check if dependencies for the certificate management step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    try:
        # Check for certbot
        certbot_check = subprocess.run(
            ["certbot", "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if certbot_check.returncode != 0:
            logger.warning("certbot is not installed")
            return False
            
        logger.info(f"Certbot version: {certbot_check.stdout.strip()}")
        
        # Check for OpenSSL
        openssl_check = subprocess.run(
            ["openssl", "version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if openssl_check.returncode != 0:
            logger.warning("OpenSSL is not installed")
            return False
            
        logger.info(f"OpenSSL version: {openssl_check.stdout.strip()}")
        
        # All dependencies are installed
        return True
            
    except FileNotFoundError:
        logger.warning("Required commands not found")
        return False
    except Exception as e:
        logger.error(f"Error checking certificate dependencies: {str(e)}")
        return False

def install_certificatestep_dependencies() -> bool:
    """
    Install dependencies for the certificate management step
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    # Skip if not on a Debian-based system
    if not os.path.exists('/etc/debian_version'):
        logger.error("Cannot install packages on non-Debian system")
        return False
        
    try:
        # Update package lists
        subprocess.run(['apt-get', 'update'], check=True)
        
        # Install required packages
        packages = [
            'certbot',
            'openssl',
            'python3-openssl',
            'acl',  # For setting proper permissions
        ]
        
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        # Verify installation
        return check_certificatestep_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install certificate dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install certificate dependencies: {str(e)}")
        return False
