import os
import sys
import platform
from typing import List
from .dependencies import DependencyManager

def check_python_version() -> bool:
    """Check if Python version is 3.8 or higher"""
    return sys.version_info >= (3, 8)

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

def check_system_requirements() -> List[str]:
    """Check all system requirements and return list of issues"""
    issues = []
    
    # Check Python version
    if not check_python_version():
        issues.append("Python 3.8 or higher is required")
    
    # Check disk space
    if not check_disk_space():
        issues.append("Insufficient disk space (minimum 10GB required)")
    
    # Check dependencies using DependencyManager
    dep_manager = DependencyManager()
    dep_issues = dep_manager.check_requirements()
    if dep_issues:
        issues.extend(dep_issues)
    
    return issues

def ensure_system_ready():
    """Check system requirements and raise exception if not met"""
    issues = check_system_requirements()
    if issues:
        # If there are dependency issues, try to fix them
        dep_manager = DependencyManager()
        if dep_manager.setup_all():
            # Recheck requirements after fixing dependencies
            issues = check_system_requirements()
            if not issues:
                return
        
        # If still have issues, raise error
        raise SystemError("\n".join(["System requirements not met:"] + issues))
