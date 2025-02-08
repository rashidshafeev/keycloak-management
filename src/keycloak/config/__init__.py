# /keycloak-management/src/keycloak/config/__init__.py
from pathlib import Path
from typing import Optional
import json
import click
from .realm import RealmConfigurator
from .users import UserConfigurator
from .events import EventConfigurator
from .notifications import NotificationConfigurator

class ConfigurationManager:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("realm-config")
        self.components = {
            "realm": RealmConfigurator,
            "users": UserConfigurator,
            "events": EventConfigurator,
            "notifications": NotificationConfigurator
        }

    def configure_all(self, interactive: bool = False):
        """Run all configuration steps"""
        for name, configurator_class in self.components.items():
            click.echo(f"\nConfiguring {name}...")
            configurator = configurator_class(self.config_dir)
            configurator.configure(interactive)

    def configure_component(self, component: str, interactive: bool = False):
        """Configure specific component"""
        if component not in self.components:
            raise ValueError(f"Unknown component: {component}")
        
        configurator = self.components[component](self.config_dir)
        configurator.configure(interactive)