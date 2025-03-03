#!/usr/bin/env python3
import click
import logging
import sys
import traceback
import importlib

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Enable debug-level logging for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("kcmanage")

@click.group()
def cli():
    """Keycloak Management CLI"""
    logger.debug("Starting kcmanage CLI")
    
    # Log Python environment details to help with debugging
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Python executable: {sys.executable}")
    logger.debug(f"Python path: {sys.path}")
    
    # Check for critical dependencies
    try:
        logger.debug("Checking for OpenSSL...")
        import ssl
        logger.debug(f"SSL version: {ssl.OPENSSL_VERSION}")
    except ImportError as e:
        logger.error(f"SSL module import error: {e}")
        logger.debug(traceback.format_exc())
        click.echo("ERROR: OpenSSL module not available. You may need to install libssl-dev/openssl-devel package.", err=True)
    
    # Try to import OpenSSL directly to check if it's the specific issue
    try:
        logger.debug("Attempting to import OpenSSL directly...")
        import OpenSSL
        logger.debug("OpenSSL module imported successfully")
    except ImportError as e:
        logger.error(f"OpenSSL import error: {e}")
        logger.debug(traceback.format_exc())
        click.echo("ERROR: Python OpenSSL module not available. Try running: pip install pyOpenSSL", err=True)
    
    logger.debug("CLI initialization complete")
    pass

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
        logger.debug(traceback.format_exc())
        # Continue to try other commands even if one fails
        continue
    except Exception as e:
        logger.error(f"Error importing {cmd_name} command: {e}")
        logger.debug(traceback.format_exc())
        continue

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
