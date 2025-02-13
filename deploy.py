#!/usr/bin/env python3

import click
import logging
from pathlib import Path
from src.deployment.orchestrator import DeploymentOrchestrator

@click.command()
@click.option("--domain", required=True,
              help="Domain name for Keycloak deployment")
@click.option("--email", required=True,
              help="Admin email for SSL certificate and notifications")
@click.option("--config", type=click.Path(exists=True),
              default="/etc/keycloak/config.yaml",
              help="Path to configuration file")
def deploy(domain: str, email: str, config: str):
    """Deploy Keycloak with all required components"""
    config_path = Path(config)
    
    # Create default config if it doesn't exist
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(f"""
domain: {domain}
admin_email: {email}
ssl:
  enabled: true
  provider: letsencrypt
monitoring:
  enabled: true
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
""")
    
    orchestrator = DeploymentOrchestrator(config_path)
    
    try:
        if orchestrator.deploy():
            click.echo("Deployment completed successfully!")
        else:
            click.echo("Deployment failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Deployment failed: {str(e)}", err=True)
        exit(1)

if __name__ == "__main__":
    deploy()