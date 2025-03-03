"""
Enhanced logging utilities for the Keycloak Management tool.

This module provides standardized logging functionality that can be
used across the codebase for consistent logging behavior.
"""

import logging
import sys
import os
import traceback
import platform
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Configure default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def configure_logger(
    name: str, 
    level: int = logging.INFO,
    format_str: str = DEFAULT_LOG_FORMAT,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with standardized settings.
    
    Args:
        name: The name of the logger
        level: The logging level (default: INFO)
        format_str: The logging format string
        log_to_file: Whether to log to a file in addition to stdout
        log_file: Optional path to a log file
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if not log_file:
            # Default log file location
            install_dir = os.environ.get('INSTALL_DIR', '/opt/fawz/keycloak')
            logs_dir = Path(install_dir) / 'logs'
            logs_dir.mkdir(exist_ok=True, parents=True)
            log_file = logs_dir / f"{name.replace('.', '_')}.log"
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_environment_info() -> Dict[str, Any]:
    """
    Get information about the Python environment.
    
    Returns:
        Dictionary containing environment information
    """
    info = {
        'python_version': sys.version,
        'python_executable': sys.executable,
        'python_path': sys.path,
        'platform': platform.platform(),
        'cwd': os.getcwd()
    }
    
    return info

def log_environment_info(logger: logging.Logger) -> None:
    """
    Log environment information using the provided logger.
    
    Args:
        logger: The logger to use
    """
    info = get_environment_info()
    
    logger.debug("Python environment information:")
    logger.debug(f"Python version: {info['python_version']}")
    logger.debug(f"Python executable: {info['python_executable']}")
    logger.debug(f"Platform: {info['platform']}")
    logger.debug(f"Current working directory: {info['cwd']}")
    logger.debug(f"Python path: {info['python_path']}")

def check_module_dependencies(
    logger: logging.Logger,
    dependencies: List[str]
) -> Dict[str, bool]:
    """
    Check if required Python modules are available.
    
    Args:
        logger: The logger to use
        dependencies: List of module names to check
        
    Returns:
        Dictionary mapping module names to availability (True/False)
    """
    results = {}
    
    for module_name in dependencies:
        try:
            # Try to import the module
            importlib.import_module(module_name)
            logger.debug(f"Module {module_name} is available")
            results[module_name] = True
        except ImportError as e:
            logger.error(f"Module {module_name} import error: {e}")
            logger.debug(traceback.format_exc())
            results[module_name] = False
            
    return results

def format_exception(e: Exception) -> str:
    """
    Format an exception with traceback for logging.
    
    Args:
        e: The exception to format
        
    Returns:
        Formatted exception string
    """
    return f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

def log_exception(logger: logging.Logger, e: Exception, msg: str = "An error occurred") -> None:
    """
    Log an exception with traceback.
    
    Args:
        logger: The logger to use
        e: The exception to log
        msg: Optional message to include
    """
    logger.error(f"{msg}: {type(e).__name__}: {e}")
    logger.debug(traceback.format_exc())

class EnhancedLogger:
    """
    Enhanced logger class that wraps a standard logger with additional functionality.
    
    This class provides a consistent interface for logging with built-in
    exception handling, environment information, and dependency checking.
    """
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_to_file: bool = False,
        log_file: Optional[str] = None
    ):
        """
        Initialize an enhanced logger.
        
        Args:
            name: Logger name
            level: Logging level
            log_to_file: Whether to log to a file
            log_file: Optional log file path
        """
        self.logger = configure_logger(
            name=name,
            level=level,
            log_to_file=log_to_file,
            log_file=log_file
        )
        self.name = name
    
    def set_level(self, level: int) -> None:
        """Set the logging level."""
        self.logger.setLevel(level)
    
    def debug(self, msg: str) -> None:
        """Log a debug message."""
        self.logger.debug(msg)
        
    def info(self, msg: str) -> None:
        """Log an info message."""
        self.logger.info(msg)
        
    def warning(self, msg: str) -> None:
        """Log a warning message."""
        self.logger.warning(msg)
        
    def error(self, msg: str) -> None:
        """Log an error message."""
        self.logger.error(msg)
        
    def critical(self, msg: str) -> None:
        """Log a critical message."""
        self.logger.critical(msg)
    
    def exception(self, e: Exception, msg: str = "An error occurred") -> None:
        """Log an exception with traceback."""
        log_exception(self.logger, e, msg)
    
    def log_environment(self) -> None:
        """Log information about the Python environment."""
        log_environment_info(self.logger)
    
    def check_dependencies(self, dependencies: List[str]) -> Dict[str, bool]:
        """Check and log availability of required modules."""
        return check_module_dependencies(self.logger, dependencies)


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> EnhancedLogger:
    """
    Get an enhanced logger instance.
    
    This is the main function to use when you need a logger in your module.
    
    Args:
        name: Logger name
        level: Logging level
        log_to_file: Whether to log to a file
        log_file: Optional log file path
        
    Returns:
        An EnhancedLogger instance
    """
    return EnhancedLogger(name, level, log_to_file, log_file)
