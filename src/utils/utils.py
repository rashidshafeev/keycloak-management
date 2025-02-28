"""
Utils module containing shared utility functions used across different steps
"""
import os
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def save_state(state_file: str, state: Dict[str, Any]) -> bool:
    """
    Save state to a JSON file
    
    Args:
        state_file: Path to the state file
        state: State dictionary to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        state_dir = os.path.dirname(state_file)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
            
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {str(e)}")
        return False

def load_state(state_file: str) -> Dict[str, Any]:
    """
    Load state from a JSON file
    
    Args:
        state_file: Path to the state file
        
    Returns:
        State dictionary, or empty dict if file doesn't exist
    """
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load state: {str(e)}")
    
    return {}

def is_root() -> bool:
    """
    Check if the current user is root
    
    Returns:
        True if current user is root, False otherwise
    """
    return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

def is_debian_based() -> bool:
    """
    Check if the system is Debian-based
    
    Returns:
        True if the system is Debian-based, False otherwise
    """
    return os.path.exists('/etc/debian_version')

def is_in_container() -> bool:
    """
    Check if running inside a container
    
    Returns:
        True if running inside a container, False otherwise
    """
    return (
        os.path.exists('/.dockerenv') or 
        (os.path.exists('/proc/1/cgroup') and 
         any('docker' in line for line in open('/proc/1/cgroup', 'r').readlines()))
    )

def get_system_info() -> Dict[str, str]:
    """
    Get basic system information
    
    Returns:
        Dictionary with system information
    """
    import platform
    import socket
    
    return {
        'hostname': socket.gethostname(),
        'os': platform.system(),
        'os_release': platform.release(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'is_debian': str(is_debian_based()),
        'is_container': str(is_in_container()),
    }