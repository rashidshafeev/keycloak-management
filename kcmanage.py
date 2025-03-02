#!/usr/bin/env python3

import click
import logging
import os
import subprocess
from pathlib import Path
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("kcmanage")

# Import core components
from src.core.orchestrator import StepOrchestrator
from src.utils.environment import get_environment_manager
from src.core.summary import InstallationSummaryGenerator

def load_environment():
    """Initialize or load environment configuration"""
    env_file = Path('.env')
    env_manager = get_environment_manager()
    
    # Load environment variables
    if env_file.exists():
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
        return env_vars
    else:
        return {}

@click.group()
def cli():
    """Keycloak Management CLI"""
    pass

@cli.command()
def setup():
    """Initial setup and configuration"""
    try:
        # Load basic environment 
        env_vars = load_environment()
        
        # Create orchestrator with minimum configuration
        orchestrator = StepOrchestrator({
            "MODE": "setup",
            "INSTALL_ROOT": env_vars.get("INSTALL_ROOT", "/opt/keycloak")
        })
        
        # Import and add system step
        from src.steps.system import SystemPreparationStep
        orchestrator.add_step(SystemPreparationStep())
        
        # Execute setup steps
        if orchestrator.execute():
            click.echo("Setup completed successfully!")
        else:
            click.echo("Setup failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Setup failed: {str(e)}", err=True)
        logger.exception("Setup failed with exception")
        exit(1)

@cli.command()
def deploy():
    """Deploy Keycloak with all required components"""
    try:
        # Load environment
        env_vars = load_environment()
        
        # Create orchestrator
        orchestrator = StepOrchestrator(env_vars)
        
        # Import and add deployment steps
        # Each step will manage its own dependencies and environment variables
        from src.steps.system import SystemPreparationStep
        from src.steps.docker import DockerSetupStep
        from src.steps.keycloak import KeycloakDeployStep
        from src.steps.firewall import FirewallStep
        
        # Add steps in execution order
        orchestrator.add_step(SystemPreparationStep())
        orchestrator.add_step(DockerSetupStep())
        orchestrator.add_step(FirewallStep())
        orchestrator.add_step(KeycloakDeployStep())
        
        # TODO: Add other steps
        # orchestrator.add_step(CertificateStep())
        # orchestrator.add_step(MonitoringStep())
        # orchestrator.add_step(BackupStep())
        
        # Execute deployment
        if orchestrator.execute():
            click.echo("Deployment completed successfully!")
        else:
            click.echo("Deployment failed!", err=True)
            exit(1)
    except Exception as e:
        click.echo(f"Deployment failed: {str(e)}", err=True)
        logger.exception("Deployment failed with exception")
        exit(1)

@cli.command()
def status():
    """Check the status of Keycloak deployment"""
    try:
        # Load environment
        env_vars = load_environment()
        
        # Simple status check using Docker
        import subprocess
        
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

@cli.command()
def backup():
    """Create a backup of Keycloak data"""
    try:
        # Load environment
        env_vars = load_environment()
        
        # Simple backup implementation
        import subprocess
        import datetime
        
        click.echo("Creating backup of Keycloak data...")
        
        backup_dir = Path(env_vars.get("BACKUP_STORAGE_PATH", "./backups"))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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

@cli.command()
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
            mtime = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
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

@cli.command()
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
        
        # Check if we need to reinstall dependencies
        requirements_file = repo_dir / "requirements.txt"
        if requirements_file.exists():
            if click.confirm("Would you like to update Python dependencies?", default=True):
                venv_dir = repo_dir / "venv"
                if venv_dir.exists():
                    click.echo("Updating Python dependencies...")
                    pip_result = subprocess.run(
                        [f"{venv_dir}/bin/pip", "install", "-r", "requirements.txt"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if pip_result.returncode != 0:
                        click.echo(f"Warning: Failed to update Python dependencies: {pip_result.stderr}", err=True)
                    else:
                        click.echo("Python dependencies updated successfully")
        
    except Exception as e:
        click.echo(f"Update failed: {str(e)}", err=True)
        logger.exception("Update failed with exception")
        exit(1)

@cli.command()
def summary():
    """Generate an installation summary"""
    try:
        # Load environment
        env_vars = load_environment()
        
        # Create summary generator
        summary_generator = InstallationSummaryGenerator(env_vars)
        
        if summary_generator.generate():
            click.echo("Installation summary generated successfully!")
            summary_path = Path(env_vars.get('INSTALL_ROOT', '/opt/keycloak')) / 'installation_summary.md'
            click.echo(f"Summary file: {summary_path}")
        else:
            click.echo("Failed to generate installation summary", err=True)
            exit(1)
            
    except Exception as e:
        click.echo(f"Failed to generate summary: {str(e)}", err=True)
        logger.exception("Summary generation failed with exception")
        exit(1)

if __name__ == "__main__":
    cli()
