from typing import Dict, Any, List
from .base import KeycloakConfigStep
from .validation import ValidationError

class ClientConfigStep(KeycloakConfigStep):
    """Handles configuration of Keycloak clients.
    
    This step manages client applications in Keycloak, including:
    - Client creation and updates
    - Client protocol settings (OpenID Connect, SAML)
    - Client authentication settings
    - Client scope mappings
    - Client service accounts
    """
    
    def __init__(self):
        super().__init__("clients", ["realm"])
        
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate client configuration against schema and business rules."""
        if not isinstance(config.get('clients'), list):
            raise ValidationError("Clients configuration must be a list")
            
        for client in config['clients']:
            if not isinstance(client.get('clientId'), str):
                raise ValidationError("Client ID must be a string")
            if not isinstance(client.get('protocol'), str):
                raise ValidationError("Client protocol must be a string")
            if client['protocol'] not in ['openid-connect', 'saml']:
                raise ValidationError("Client protocol must be either 'openid-connect' or 'saml'")
                
        return True
        
    def _get_existing_client(self, client_id: str) -> Dict[str, Any]:
        """Get existing client configuration from Keycloak."""
        result = self.kcadm.get(f'clients?clientId={client_id}')
        if not result:
            return None
        return result[0] if result else None
        
    def _create_client(self, client: Dict[str, Any]) -> None:
        """Create a new client in Keycloak."""
        self.kcadm.create('clients', client)
        
    def _update_client(self, client_id: str, client: Dict[str, Any]) -> None:
        """Update an existing client in Keycloak."""
        existing = self._get_existing_client(client_id)
        if not existing:
            raise ValidationError(f"Client {client_id} not found")
        self.kcadm.update(f'clients/{existing["id"]}', client)
        
    def execute(self, config: Dict[str, Any]) -> None:
        """Apply client configuration to Keycloak."""
        for client in config['clients']:
            client_id = client['clientId']
            existing = self._get_existing_client(client_id)
            
            if existing:
                self._update_client(client_id, client)
            else:
                self._create_client(client)
                
    def rollback(self) -> None:
        """Rollback client configuration changes."""
        # For now, we don't implement rollback as it could affect running applications
        # In the future, we could store the previous state and restore it
        pass
