import click
import sys
from ..utils.environment import load_environment
from ..utils.logger import get_logger

# Set up enhanced logger
logger = get_logger("kcmanage.deploy")

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--step', type=str, help='Run only a specific deployment step')
@click.option('--dry-run', is_flag=True, help='Check what would be deployed without making changes')
def deploy(verbose, step, dry_run):
    """Deploy Keycloak with all required components"""
    logger.info("Starting deploy command")
    
    if verbose:
        logger.set_level("DEBUG")
        logger.debug("Verbose logging enabled")
    
    if dry_run:
        logger.info("Dry run mode enabled - no changes will be made")
    
    try:
        # Load environment
        logger.debug("Loading environment variables")
        env_vars = load_environment()
        logger.debug(f"Loaded {len(env_vars)} environment variables")
        
        # Log Python environment details
        logger.log_environment()
        
        # Check dependencies
        dependencies = ['ssl', 'OpenSSL', 'src.core.orchestrator']
        logger.check_dependencies(dependencies)
        
        # Try importing the orchestrator
        logger.debug("Importing orchestrator module")
        try:
            from src.core.orchestrator import StepOrchestrator
            logger.debug("Successfully imported StepOrchestrator")
        except ImportError as e:
            logger.exception(e, "Failed to import orchestrator")
            click.echo(f"Deployment failed: Error importing orchestrator - {e}", err=True)
            click.echo("This may indicate an installation issue. Check that 'src' is in your Python path.", err=True)
            return 1
        
        # Create orchestrator
        logger.debug("Creating StepOrchestrator instance")
        try:
            orchestrator = StepOrchestrator(env_vars)
            if dry_run:
                orchestrator.set_dry_run(True)
            logger.debug("StepOrchestrator instance created successfully")
        except Exception as e:
            logger.exception(e, "Error creating orchestrator")
            click.echo(f"Deployment failed: Could not create orchestrator - {e}", err=True)
            return 1
        
        # Import steps with improved error handling
        logger.debug("Importing deployment steps")
        step_imports = [
            ("system", "src.steps.system", "SystemPreparationStep"),
            ("docker", "src.steps.docker", "DockerSetupStep"),
            ("firewall", "src.steps.firewall", "FirewallStep"),
            ("certificates", "src.steps.certificates", "CertificateStep"),
            ("keycloak", "src.steps.keycloak", "KeycloakDeploymentstep")
        ]
        
        steps = {}
        for step_id, module_path, class_name in step_imports:
            try:
                logger.debug(f"Importing {step_id} step from {module_path}")
                module = __import__(module_path, fromlist=[class_name])
                step_class = getattr(module, class_name)
                steps[step_id] = step_class()
                logger.debug(f"Successfully imported {step_id} step")
            except ImportError as e:
                logger.exception(e, f"Failed to import {step_id} step")
                click.echo(f"Warning: Could not import {step_id} step - {e}", err=True)
                # Continue with other steps
            except AttributeError as e:
                logger.exception(e, f"Failed to find class '{class_name}' in {module_path}")
                click.echo(f"Warning: Class '{class_name}' not found in module {module_path}", err=True)
                # Continue with other steps
                
        # Add steps to orchestrator based on filter if provided
        if step:
            logger.info(f"Running only the {step} step")
            if step not in steps:
                logger.error(f"Step '{step}' not found")
                click.echo(f"Error: Step '{step}' not found. Available steps: {', '.join(steps.keys())}", err=True)
                return 1
            orchestrator.add_step(steps[step])
        else:
            # Add all available steps in the correct order
            logger.debug("Adding all steps to orchestrator")
            for step_id in ["system", "docker", "firewall", "certificates", "keycloak"]:
                if step_id in steps:
                    logger.debug(f"Adding {step_id} step to orchestrator")
                    orchestrator.add_step(steps[step_id])
                else:
                    logger.warning(f"Step {step_id} not available - skipping")
        
        # Execute deployment
        logger.info("Starting deployment execution")
        result = orchestrator.execute()
        
        if result:
            logger.info("Deployment completed successfully")
            click.echo("Deployment completed successfully!")
            return 0
        else:
            logger.error("Deployment failed during execution")
            click.echo("Deployment failed!", err=True)
            return 1
            
    except ImportError as e:
        logger.exception(e, "Module import error")
        click.echo(f"Deployment failed: Module import error - {e}", err=True)
        click.echo("This may be due to missing system packages or Python dependencies.", err=True)
        return 1
    except Exception as e:
        logger.exception(e, "Deployment failed")
        click.echo(f"Deployment failed: {e}", err=True)
        return 1
