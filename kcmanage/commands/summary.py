import click
from pathlib import Path
from ..utils.environment import load_environment
from src.core.summary import InstallationSummaryGenerator

@click.command()
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
        exit(1)