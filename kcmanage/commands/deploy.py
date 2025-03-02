import click
from ..utils.environment import load_environment
from src.core.orchestrator import StepOrchestrator

@click.command()
def deploy():
    """Deploy Keycloak with all required components"""
    try:
        # Load environment
        env_vars = load_environment()
        
        # Create orchestrator
        orchestrator = StepOrchestrator(env_vars)
        
        # Import steps
        from src.steps.system import SystemPreparationStep
        from src.steps.docker import DockerSetupStep
        from src.steps.firewall import FirewallStep
        from src.steps.certificates import CertificateStep
        from src.steps.keycloak import KeycloakDeployStep
        from src.steps.prometheus import PrometheusStep
        from src.steps.grafana import GrafanaStep
        from src.steps.wazuh import WazuhStep
        from src.steps.backup import DatabaseBackupStep
        
        # Add core steps
        orchestrator.add_step(SystemPreparationStep())
        orchestrator.add_step(DockerSetupStep())
        orchestrator.add_step(FirewallStep())
        orchestrator.add_step(CertificateStep())
        
        # Add main deployment step
        orchestrator.add_step(KeycloakDeployStep())
        
        # Add monitoring steps (optional)
        # orchestrator.add_step(PrometheusStep())
        # orchestrator.add_step(GrafanaStep())
        
        # Add security step (optional)
        # orchestrator.add_step(WazuhStep())
        
        # Add backup step (optional)
        # orchestrator.add_step(DatabaseBackupStep())
        
        # Execute deployment
        if orchestrator.execute():
            click.echo("Deployment completed successfully!")
        else:
            click.echo("Deployment failed!", err=True)
            exit(1)
            
    except Exception as e:
        click.echo(f"Deployment failed: {str(e)}", err=True)
        exit(1)