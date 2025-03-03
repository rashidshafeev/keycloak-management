#!/usr/bin/env python3
import click
import importlib
import sys
from .utils.logger import get_logger

# Set up enhanced logging
logger = get_logger("kcmanage", level="DEBUG")

@click.group()
def cli():
    """Keycloak Management CLI"""
    logger.debug("Starting kcmanage CLI")
    
    # Log Python environment info on startup
    logger.log_environment()
    
    # Check for critical dependencies
    dependencies = ['ssl', 'OpenSSL', 'requests', 'docker']
    dependency_status = logger.check_dependencies(dependencies)
    
    # Check OpenSSL specifically
    if not dependency_status.get('OpenSSL', False):
        click.echo("WARNING: OpenSSL module not available. Some features may not work correctly.", err=True)
        click.echo("Try running: pip install pyOpenSSL", err=True)
    
    # Display a notice if docker is not available
    if not dependency_status.get('docker', False):
        click.echo("WARNING: Docker SDK not available. Deployment commands will not work.", err=True)
        click.echo("Try running: pip install docker", err=True)
    
    logger.debug("CLI initialization complete")

# Import commands with better error handling
commands_to_import = [
    ('setup', '.commands.setup'),
    ('deploy', '.commands.deploy'),
    ('status', '.commands.status'),
    ('backup', '.commands.backup'),
    ('restore', '.commands.restore'),
    ('update', '.commands.update'),
    ('summary', '.commands.summary')
]

for cmd_name, module_path in commands_to_import:
    try:
        logger.debug(f"Importing {cmd_name} command from {module_path}")
        module = importlib.import_module(module_path, package='kcmanage')
        command = getattr(module, cmd_name)
        cli.add_command(command)
        logger.debug(f"Successfully imported {cmd_name} command")
    except ImportError as e:
        logger.error(f"Failed to import {cmd_name} command: {e}")
        # Continue to try other commands even if one fails
    except Exception as e:
        logger.exception(e, f"Error importing {cmd_name} command")

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        logger.exception(e, "Unhandled exception in CLI")
        sys.exit(1)
