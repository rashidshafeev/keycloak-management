#!/usr/bin/env python3
import click
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("kcmanage")

@click.group()
def cli():
    """Keycloak Management CLI"""
    pass

# Import commands
from .commands.setup import setup
from .commands.deploy import deploy
from .commands.status import status
from .commands.backup import backup
from .commands.restore import restore
from .commands.update import update
from .commands.summary import summary

# Register commands
cli.add_command(setup)
cli.add_command(deploy)
cli.add_command(status)
cli.add_command(backup)
cli.add_command(restore)
cli.add_command(update)
cli.add_command(summary)

if __name__ == "__main__":
    cli()