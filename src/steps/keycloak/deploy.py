"""
Keycloak deployment module.

This module provides the main entry point for deploying Keycloak as a standalone step.
"""

from .keycloak_deploymentstep import KeycloakDeploymentstep

# Export the main step class
__all__ = ['KeycloakDeploymentstep']