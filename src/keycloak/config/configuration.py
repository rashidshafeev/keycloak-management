# /keycloak-management/src/keycloak/config/configuration.py
from pathlib import Path
from typing import Optional, Dict, Any
import json
import click
from dataclasses import dataclass
from .realm import RealmConfigStep
from .events import EventConfigStep
from .security import SecurityConfigStep
from .clients import ClientConfigStep
from .roles import RolesConfigStep
from .authentication import AuthenticationConfigStep
from .monitoring import MonitoringConfigStep
from .themes import ThemeConfigStep
from .smtp import SmtpConfigStep
from .yaml_loader import YamlConfigLoader

@dataclass
class ConfigStep:
    """Base class for configuration steps"""
    name: str
    description: str
    schema_file: Optional[str] = None
    dependencies: list[str] = None
    required: bool = True

class KeycloakConfigurationManager:
    """Manages Keycloak configuration using YAML templates"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config/templates")
        self.yaml_loader = YamlConfigLoader(self.config_dir)
        
        # Define configuration steps with dependencies
        self.steps = {
            "realm": ConfigStep(
                name="realm",
                description="Basic realm settings",
                schema_file="realm_schema.json"
            ),
            "security": ConfigStep(
                name="security",
                description="Security settings and policies",
                schema_file="security_schema.json"
            ),
            "clients": ConfigStep(
                name="clients",
                description="Client applications",
                dependencies=["realm"],
                schema_file="clients_schema.json"
            ),
            "roles": ConfigStep(
                name="roles",
                description="Role definitions",
                dependencies=["realm"],
                schema_file="roles_schema.json"
            ),
            "authentication": ConfigStep(
                name="authentication",
                description="Authentication flows",
                dependencies=["realm", "security"],
                schema_file="authentication_schema.json"
            ),
            "events": ConfigStep(
                name="events",
                description="Event listeners and settings",
                schema_file="events_schema.json"
            ),
            "monitoring": ConfigStep(
                name="monitoring",
                description="Metrics and health checks",
                required=False,
                schema_file="monitoring_schema.json"
            ),
            "themes": ConfigStep(
                name="themes",
                description="Custom themes",
                required=False,
                schema_file="themes_schema.json"
            ),
            "smtp": ConfigStep(
                name="smtp",
                description="Email settings",
                required=False,
                schema_file="smtp_schema.json"
            )
        }
        
        # Map steps to their configurator classes
        self.configurators = {
            "realm": RealmConfigStep,
            "security": SecurityConfigStep,
            "clients": ClientConfigStep,
            "roles": RolesConfigStep,
            "authentication": AuthenticationConfigStep,
            "events": EventConfigStep,
            "monitoring": MonitoringConfigStep,
            "themes": ThemeConfigStep,
            "smtp": SmtpConfigStep
        }
        
        self.config_cache: Dict[str, Any] = {}

    def validate_dependencies(self, step: str) -> bool:
        """Check if all dependencies for a step are satisfied"""
        step_config = self.steps[step]
        if not step_config.dependencies:
            return True
            
        for dep in step_config.dependencies:
            if dep not in self.config_cache:
                return False
        return True

    def configure_all(self, interactive: bool = False):
        """Run all configuration steps in correct order"""
        # Reset config cache
        self.config_cache = {}
        
        # Process required steps first, respecting dependencies
        required_steps = [name for name, step in self.steps.items() if step.required]
        optional_steps = [name for name, step in self.steps.items() if not step.required]
        
        for step_name in required_steps + optional_steps:
            if not self.validate_dependencies(step_name):
                click.echo(f"Skipping {step_name}: dependencies not satisfied")
                continue
                
            click.echo(f"\nConfiguring {step_name}...")
            try:
                # Load and validate YAML config
                config = self.yaml_loader.load_config(step_name)
                if self.steps[step_name].schema_file:
                    self.yaml_loader.validate_schema(config, self.steps[step_name].schema_file)
                
                # Cache config for dependency resolution
                self.config_cache[step_name] = config
                
                # Apply configuration
                configurator = self.configurators[step_name](self.config_dir)
                configurator.configure(interactive, config)
                
            except FileNotFoundError:
                if self.steps[step_name].required:
                    raise click.ClickException(f"Required config {step_name}.yml not found")
                click.echo(f"Optional config {step_name}.yml not found, skipping...")
            except Exception as e:
                raise click.ClickException(f"Error configuring {step_name}: {str(e)}")

    def configure_component(self, component: str, interactive: bool = False):
        """Configure specific component"""
        if component not in self.steps:
            raise ValueError(f"Unknown component: {component}")
            
        if not self.validate_dependencies(component):
            raise click.ClickException(f"Dependencies not satisfied for {component}")
            
        try:
            # Load and validate YAML config
            config = self.yaml_loader.load_config(component)
            if self.steps[component].schema_file:
                self.yaml_loader.validate_schema(config, self.steps[component].schema_file)
            
            # Apply configuration
            configurator = self.configurators[component](self.config_dir)
            configurator.configure(interactive, config)
            
        except FileNotFoundError:
            if self.steps[component].required:
                raise click.ClickException(f"Required config {component}.yml not found")
            click.echo(f"Optional config {component}.yml not found, skipping...")
        except Exception as e:
            raise click.ClickException(f"Error configuring {component}: {str(e)}")