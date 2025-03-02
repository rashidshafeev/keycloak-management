from typing import Dict, Any, List
from .base import KeycloakConfigStep
from .validation import ValidationError

class IdentityProviderConfigStep(KeycloakConfigStep):
    """Handles configuration of Keycloak identity providers.
    
    This step manages identity provider configuration in Keycloak, including:
    - Social providers (Google, Facebook, etc.)
    - OIDC providers
    - SAML providers
    - Provider-specific settings
    - Authentication flows
    """
    
    VALID_PROVIDERS = {
        'google', 'facebook', 'github', 'microsoft', 'twitter',
        'linkedin', 'oidc', 'saml', 'keycloak-oidc'
    }
    
    def __init__(self):
        super().__init__("identity-providers", ["realm", "authentication"])
        
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate identity provider configuration against schema and business rules."""
        providers = config.get('identityProviders', [])
        if not isinstance(providers, list):
            raise ValidationError("Identity providers configuration must be a list")
            
        for provider in providers:
            if not isinstance(provider.get('alias'), str):
                raise ValidationError("Provider alias must be a string")
            if not isinstance(provider.get('providerId'), str):
                raise ValidationError("Provider ID must be a string")
            if provider['providerId'] not in self.VALID_PROVIDERS:
                raise ValidationError(f"Invalid provider ID: {provider['providerId']}")
                
            # Validate provider-specific config
            config = provider.get('config', {})
            if provider['providerId'] in {'oidc', 'keycloak-oidc'}:
                if not config.get('clientId'):
                    raise ValidationError("OIDC provider must have clientId")
                if not config.get('clientSecret'):
                    raise ValidationError("OIDC provider must have clientSecret")
                    
            elif provider['providerId'] == 'saml':
                if not config.get('entityId'):
                    raise ValidationError("SAML provider must have entityId")
                if not config.get('singleSignOnServiceUrl'):
                    raise ValidationError("SAML provider must have singleSignOnServiceUrl")
                    
        return True
        
    def _get_existing_provider(self, alias: str) -> Dict[str, Any]:
        """Get existing identity provider from Keycloak."""
        result = self.kcadm.get(f'identity-provider/instances/{alias}')
        return result if result else None
        
    def _create_provider(self, provider: Dict[str, Any]) -> None:
        """Create a new identity provider in Keycloak."""
        self.kcadm.create('identity-provider/instances', provider)
        
    def _update_provider(self, alias: str, provider: Dict[str, Any]) -> None:
        """Update an existing identity provider in Keycloak."""
        existing = self._get_existing_provider(alias)
        if not existing:
            raise ValidationError(f"Provider {alias} not found")
        self.kcadm.update(f'identity-provider/instances/{alias}', provider)
        
    def execute(self, config: Dict[str, Any]) -> None:
        """Apply identity provider configuration to Keycloak."""
        for provider in config.get('identityProviders', []):
            alias = provider['alias']
            existing = self._get_existing_provider(alias)
            
            if existing:
                self._update_provider(alias, provider)
            else:
                self._create_provider(provider)
                
    def rollback(self) -> None:
        """Rollback identity provider configuration changes."""
        # For now, we don't implement rollback as it could affect running authentication
        # In the future, we could store the previous state and restore it
        pass
