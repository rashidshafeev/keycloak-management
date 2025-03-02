import click
import subprocess
import os
from pathlib import Path
from ..utils.environment import load_environment

@click.command()
def update():
    """Update the Keycloak Management software (git pull)"""
    try:
        # Get the installation directory
        install_dir = os.environ.get('INSTALL_DIR', '/opt/fawz/keycloak')
        
        click.echo(f"Updating Keycloak Management software in {install_dir}...")
        
        # Check if directory exists and is a git repository
        repo_dir = Path(install_dir)
        git_dir = repo_dir / ".git"
        if not repo_dir.exists() or not git_dir.exists():
            click.echo(f"Error: {install_dir} is not a valid git repository", err=True)
            exit(1)
            
        # Change to repository directory
        os.chdir(install_dir)
        
        # Run git pull
        result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            click.echo(f"Git pull failed: {result.stderr}", err=True)
            exit(1)
            
        click.echo(result.stdout)
        click.echo("Update completed successfully!")