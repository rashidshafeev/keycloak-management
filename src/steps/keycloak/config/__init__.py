"""
Keycloak configuration modules.

This package contains modules for configuring Keycloak instances, including:
- Realm configuration
- Client applications
- Authentication flows
- Roles and permissions
- SMTP settings
- Security settings
"""

from .realm import RealmConfig
from .clients import ClientsConfig
from .roles import RolesConfig
from .authentication import AuthenticationConfig
from .smtp import SmtpConfig
from .security import SecurityConfig
from .monitoring import MonitoringConfig
from .events import EventsConfig
from .themes import ThemesConfig
from .identity_providers import IdentityProvidersConfig

__all__ = [
    'RealmConfig',
    'ClientsConfig',
    'RolesConfig',
    'AuthenticationConfig',
    'SmtpConfig',
    'SecurityConfig',
    'MonitoringConfig',
    'EventsConfig',
    'ThemesConfig',
    'IdentityProvidersConfig'
]