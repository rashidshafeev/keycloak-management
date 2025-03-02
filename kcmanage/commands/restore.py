import click
import subprocess
from pathlib import Path
from datetime import datetime
from ..utils.environment import load_environment

@click.command()
def restore():
    """Restore Keycloak from a backup"""
    try:
        # Load environment
        env_vars = load_environment()
        
        backup_dir = Path(env_vars.get("BACKUP_STORAGE_PATH", "./backups"))
        if not backup_dir.exists():
            click.echo(f"Backup directory {backup_dir} does not exist", err=True)
            exit(1)
            
        # List available backups
        backups = list(backup_dir.glob("keycloak_backup_*.sql"))
        if not backups:
            click.echo("No backups found", err=True)
            exit(1)
            
        # Sort by modification time (newest first)
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        click.echo("Available backups:")
        for i, backup in enumerate(backups):
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            click.echo(f"{i+1}. {backup.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
        # Select backup
        selection = click.prompt("Select backup to restore (number)", type=int, default=1)
        if selection < 1 or selection > len(backups):
            click.echo(f"Invalid selection: {selection}", err=True)
            exit(1)
            
        selected_backup = backups[selection-1]
        
        # Confirm
        if not click.confirm(f"Are you sure you want to restore from {selected_backup.name}?"):
            click.echo("Restore cancelled")
            exit(0)
            
        # Stop Keycloak
        click.echo("Stopping Keycloak...")
        subprocess.run(['docker', 'stop', 'keycloak'], check=False)
        
        # Restore database
        click.echo("Restoring database...")
        try:
            # Import with docker
            with open(selected_backup, 'r') as f:
                cmd = [
                    'docker', 'exec', '-i', 'keycloak-postgres',
                    'psql', '-U', 'keycloak', '-d', 'keycloak'
                ]
                result = subprocess.run(cmd, stdin=f, check=True)
                
            click.echo("Database restored successfully")
            
            # Start Keycloak
            click.echo("Starting Keycloak...")
            subprocess.run(['docker', 'start', 'keycloak'], check=True)
            
            click.echo("Restore completed successfully")
            
        except Exception as e:
            click.echo(f"Restore failed: {str(e)}", err=True)
            click.echo("Attempting to start Keycloak to recover...")
            subprocess.run(['docker', 'start', 'keycloak'], check=False)
            exit(1)
            
    except Exception as e:
        click.echo(f"Restore failed: {str(e)}", err=True)
        exit(1)