# Enhanced Logging System

The Keycloak Management tool includes a robust logging system that standardizes logging across all components. This document explains how to use the logging utilities in your code.

## Basic Usage

To use the enhanced logging in your module:

```python
from kcmanage.utils.logger import get_logger

# Create a logger with your module name (follow the hierarchy pattern)
logger = get_logger("kcmanage.your_module")

# Use the logger in your code
logger.info("Starting operation")
logger.debug("Detailed debugging information")
logger.warning("Something unexpected but non-critical happened")
logger.error("An error occurred")

# Log exceptions with tracebacks
try:
    # Some code that might raise an exception
    result = some_function()
except Exception as e:
    logger.exception(e, "Operation failed")
```

## Logger Configuration

The `get_logger` function accepts several parameters:

```python
logger = get_logger(
    name="kcmanage.module",     # Required: Logger name
    level=logging.INFO,         # Optional: Log level (default: INFO)
    log_to_file=False,          # Optional: Whether to log to a file as well
    log_file=None               # Optional: Custom log file path
)
```

## Environment Information

The enhanced logger includes utilities for logging environment information:

```python
# Log Python environment details (version, path, etc.)
logger.log_environment()
```

## Dependency Checking

You can check for required dependencies:

```python
# Check if required modules are available
dependencies = ['ssl', 'OpenSSL', 'requests', 'docker']
dependency_status = logger.check_dependencies(dependencies)

# Check results
if not dependency_status.get('docker', False):
    print("Docker SDK not available, deployment commands will not work")
```

## Verbose Mode with Click Commands

For Click commands, you can easily implement a verbose flag:

```python
@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def your_command(verbose):
    """Your command description"""
    
    # Get a logger for your command
    logger = get_logger("kcmanage.your_command")
    
    # Set log level based on verbose flag
    if verbose:
        logger.set_level(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Your command logic...
```

## Exception Handling

The enhanced logger provides better exception handling:

```python
try:
    # Your code
except Exception as e:
    # Log the exception with a custom message
    logger.exception(e, "Failed to process data")
    
    # You can still raise or return an error code
    return 1
```

## Where Logs are Stored

By default, logs are sent to stdout. If you enable file logging:

```python
logger = get_logger("kcmanage.module", log_to_file=True)
```

Logs will be stored in:

```
/opt/fawz/keycloak/logs/kcmanage_module.log
```

You can also specify a custom log file path:

```python
logger = get_logger("kcmanage.module", log_to_file=True, log_file="/path/to/custom.log")
```

## Best Practices

1. **Use Hierarchical Names**: Follow the pattern `kcmanage.module.submodule` for logger names.

2. **Log at Appropriate Levels**:
   - `DEBUG`: Detailed information, only useful when troubleshooting
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: Unexpected situation that doesn't prevent operation
   - `ERROR`: Error that prevented a function from working
   - `CRITICAL`: Critical error that prevents the program from continuing

3. **Include Context**: Log messages should provide enough context to understand what's happening.

4. **Use Exception Logging**: Always use `logger.exception()` for exceptions to include tracebacks.

5. **Enable Verbose Mode**: For commands, allow users to enable verbose output with a flag.

## Implementation Details

The enhanced logging system is implemented in `kcmanage/utils/logger.py` and includes:

1. `EnhancedLogger`: A class that wraps the standard Python logger with additional functionality.
2. `get_logger()`: The main function to get a logger instance.
3. Utility functions for environment information and dependency checking.
4. Standardized formatting and output handling.

This implementation ensures consistent logging behavior across all components of the Keycloak Management tool.
