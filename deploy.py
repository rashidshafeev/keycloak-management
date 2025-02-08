#!/usr/bin/env python3

import click
import logging
from pathlib import Path
from src.deployment.orchestrator import DeploymentOrchestrator

@click.command()
@click.option("--config", type=click.Path(exists=True), required=True,
              help="Path to configuration file")
def deploy(config: str):
    """Deploy Keycloak with all required components"""
    config_path = Path(config)
    orchestrator = DeploymentOrchestrator(config_path)
    
    try:
        if orchestrator.deploy():
            click.echo("Deployment completed successfully!")
        else:
            click.echo("Deployment failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Deployment failed: {e}", err=True)
        exit(1)

if __name__ == "__main__":
    deploy()