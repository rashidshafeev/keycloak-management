#!/usr/bin/env python3

import click
import logging
from pathlib import Path
from src.deployment.orchestrator import DeploymentOrchestrator
from src.utils.system_checks import ensure_system_ready
from src.utils.environment import EnvironmentSetup, load_environment

def init_environment():
    """Initialize or load environment configuration"""
    env_file = Path('.env')
    if not env_file.exists():
        click.echo("No .env file found. Starting setup...")
        env_setup = EnvironmentSetup()
        if not env_setup.setup():
            raise click.ClickException("Environment setup failed")
        return load_environment()
    
    try:
        env_vars = load_environment()
        # Check for required variables
        required_vars = [
            'KEYCLOAK_DOMAIN',
            'KEYCLOAK_ADMIN_EMAIL',
            'KEYCLOAK_ADMIN_PASSWORD',
            'DB_PASSWORD'
        ]
        missing_vars = [var for var in required_vars if var not in env_vars]
        if missing_vars:
            click.echo(f"Missing required variables: {', '.join(missing_vars)}")
            click.echo("Starting setup to configure missing variables...")
            env_setup = EnvironmentSetup()
            if not env_setup.setup():
                raise click.ClickException("Environment setup failed")
            return load_environment()
        return env_vars
    except Exception as e:
        raise click.ClickException(f"Failed to load environment: {str(e)}")

@click.group()
def cli():
    """Keycloak Management CLI"""
    pass

@cli.command()
def setup():
    """Initial setup and configuration"""
    try:
        # Check system requirements and install dependencies if needed
        click.echo("Checking system requirements and installing dependencies...")
        ensure_system_ready()
        
        # Set up environment
        click.echo("Setting up environment...")
        env_setup = EnvironmentSetup()
        if env_setup.setup():
            click.echo("Setup completed successfully!")
        else:
            click.echo("Setup failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Setup failed: {str(e)}", err=True)
        exit(1)

@cli.command()
def deploy():
    """Deploy Keycloak with all required components"""
    try:
        # Check system requirements and install dependencies if needed
        ensure_system_ready()
        
        # Initialize or load environment
        env_config = init_environment()
        
        # Deploy using orchestrator with environment config
        orchestrator = DeploymentOrchestrator(env_config)
        if orchestrator.deploy():
            click.echo("Deployment completed successfully!")
        else:
            click.echo("Deployment failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Deployment failed: {str(e)}", err=True)
        exit(1)

@cli.command()
def status():
    """Check the status of Keycloak deployment"""
    try:
        ensure_system_ready()
        env_config = init_environment()
        # TODO: Implement status check
        click.echo("Status check not implemented yet")
    except Exception as e:
        click.echo(f"Status check failed: {str(e)}", err=True)
        exit(1)

@cli.command()
def backup():
    """Create a backup of Keycloak data"""
    try:
        ensure_system_ready()
        env_config = init_environment()
        # TODO: Implement backup
        click.echo("Backup not implemented yet")
    except Exception as e:
        click.echo(f"Backup failed: {str(e)}", err=True)
        exit(1)

@cli.command()
def restore():
    """Restore Keycloak from a backup"""
    try:
        ensure_system_ready()
        env_config = init_environment()
        # TODO: Implement restore
        click.echo("Restore not implemented yet")
    except Exception as e:
        click.echo(f"Restore failed: {str(e)}", err=True)
        exit(1)

if __name__ == "__main__":
    cli()
