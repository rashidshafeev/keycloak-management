import click
from ..utils.environment import load_environment
from src.core.orchestrator import StepOrchestrator

@click.command()
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
        exit(1)