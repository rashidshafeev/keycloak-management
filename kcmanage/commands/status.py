import click
import subprocess
from ..utils.environment import load_environment

@click.command()
def status():
    """Check the status of Keycloak deployment"""
    try:
        # Load environment
        env_vars = load_environment()
        
        click.echo("Checking Keycloak status...")
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=keycloak', '--format', '{{.Status}}'],
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.stdout.strip():
                click.echo(f"Keycloak is running: {result.stdout.strip()}")
            else:
                click.echo("Keycloak is not running")
                
            # Check database
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=keycloak-postgres', '--format', '{{.Status}}'],
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.stdout.strip():
                click.echo(f"Database is running: {result.stdout.strip()}")
            else:
                click.echo("Database is not running")
                
        except Exception as e:
            click.echo(f"Error checking status: {str(e)}", err=True)
            
    except Exception as e:
        click.echo(f"Status check failed: {str(e)}", err=True)
        exit(1)