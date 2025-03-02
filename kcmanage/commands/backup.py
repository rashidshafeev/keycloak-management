import click
import subprocess
from pathlib import Path
from datetime import datetime
from ..utils.environment import load_environment

@click.command()
def backup():
    """Create a backup of Keycloak data"""
    try:
        # Load environment
        env_vars = load_environment()
        
        click.echo("Creating backup of Keycloak data...")
        
        backup_dir = Path(env_vars.get("BACKUP_STORAGE_PATH", "./backups"))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"keycloak_backup_{timestamp}.sql"
        
        try:
            # Run backup through docker
            cmd = [
                'docker', 'exec', 'keycloak-postgres',
                'pg_dump', '-U', 'keycloak', 'keycloak'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, check=True)
            
            click.echo(f"Backup created successfully: {backup_file}")
            
        except Exception as e:
            click.echo(f"Backup failed: {str(e)}", err=True)
            exit(1)
            
    except Exception as e:
        click.echo(f"Backup failed: {str(e)}", err=True)
        exit(1)