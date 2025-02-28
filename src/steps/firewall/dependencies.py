import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.firewallstep.dependencies")

def check_firewallstep_dependencies() -> bool:
    """
    Check if dependencies for the firewall configuration step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    try:
        # Check for iptables
        iptables_check = subprocess.run(
            ["iptables", "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if iptables_check.returncode != 0:
            logger.warning("iptables is not installed")
            return False
            
        logger.info(f"iptables version: {iptables_check.stdout.strip()}")
        
        # Check for fail2ban (optional)
        fail2ban_check = subprocess.run(
            ["fail2ban-client", "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if fail2ban_check.returncode == 0:
            logger.info(f"fail2ban version: {fail2ban_check.stdout.strip()}")
        else:
            logger.warning("fail2ban is not installed (optional)")
        
        # We consider the check successful if iptables is available
        return iptables_check.returncode == 0
            
    except FileNotFoundError:
        logger.warning("Firewall commands not found")
        return False
    except Exception as e:
        logger.error(f"Error checking firewall dependencies: {str(e)}")
        return False

def install_firewallstep_dependencies() -> bool:
    """
    Install dependencies for the firewall configuration step
    
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
        subprocess.run([
            'apt-get', 'install', '-y',
            'iptables',
            'fail2ban'
        ], check=True)
        
        # Verify installation
        return check_firewallstep_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install firewall dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install firewall dependencies: {str(e)}")
        return False
