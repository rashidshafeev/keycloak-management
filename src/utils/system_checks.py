import os
import sys
import subprocess
import platform
from typing import List, Tuple

def check_python_version() -> bool:
    """Check if Python version is 3.8 or higher"""
    return sys.version_info >= (3, 8)

def check_docker() -> Tuple[bool, str]:
    """Check if Docker is installed and running"""
    try:
        # Check if docker command exists
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        
        # Check if docker daemon is running
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        return True, "Docker is installed and running"
    except subprocess.CalledProcessError:
        return False, "Docker is not running"
    except FileNotFoundError:
        return False, "Docker is not installed"

def check_system_requirements() -> List[str]:
    """Check all system requirements and return list of issues"""
    issues = []
    
    # Check Python version
    if not check_python_version():
        issues.append("Python 3.8 or higher is required")
    
    # Check Docker
    docker_ok, docker_msg = check_docker()
    if not docker_ok:
        issues.append(f"Docker issue: {docker_msg}")
    
    # Check disk space
    if not check_disk_space():
        issues.append("Insufficient disk space (minimum 10GB required)")
    
    return issues

def check_disk_space(min_space_gb: int = 10) -> bool:
    """Check if there's enough disk space"""
    if platform.system() == "Windows":
        # Windows-specific disk space check
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("."), None, None, ctypes.pointer(free_bytes))
        free_gb = free_bytes.value / (1024**3)
    else:
        # Unix-like systems
        st = os.statvfs(".")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
    
    return free_gb >= min_space_gb

def ensure_system_ready():
    """Check system requirements and raise exception if not met"""
    issues = check_system_requirements()
    if issues:
        raise SystemError("\n".join(["System requirements not met:"] + issues))
