from typing import Dict, Any, List
from .base import KeycloakConfigStep
from .validation import ValidationError

class AuthenticationConfigStep(KeycloakConfigStep):
    """Handles configuration of Keycloak authentication flows.
    
    This step manages authentication configuration in Keycloak, including:
    - Authentication flows
    - Required actions
    - Identity providers
    - Browser flow overrides
    """
    
    def __init__(self):
        super().__init__("authentication", ["realm"])
        
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate authentication configuration against schema and business rules."""
        auth_config = config.get('authentication', {})
        
        # Validate flows
        flows = auth_config.get('flows', [])
        if not isinstance(flows, list):
            raise ValidationError("Authentication flows must be a list")
            
        for flow in flows:
            if not isinstance(flow.get('alias'), str):
                raise ValidationError("Flow alias must be a string")
            if not isinstance(flow.get('providerId'), str):
                raise ValidationError("Flow providerId must be a string")
            if not isinstance(flow.get('description'), str):
                raise ValidationError("Flow description must be a string")
                
        # Validate required actions
        actions = auth_config.get('requiredActions', [])
        if not isinstance(actions, list):
            raise ValidationError("Required actions must be a list")
            
        for action in actions:
            if not isinstance(action.get('alias'), str):
                raise ValidationError("Action alias must be a string")
            if not isinstance(action.get('name'), str):
                raise ValidationError("Action name must be a string")
                
        return True
        
    def _get_existing_flow(self, alias: str) -> Dict[str, Any]:
        """Get existing authentication flow from Keycloak."""
        result = self.kcadm.get(f'authentication/flows/{alias}')
        return result if result else None
        
    def _create_flow(self, flow: Dict[str, Any]) -> None:
        """Create a new authentication flow in Keycloak."""
        self.kcadm.create('authentication/flows', flow)
        
    def _update_flow(self, alias: str, flow: Dict[str, Any]) -> None:
        """Update an existing authentication flow in Keycloak."""
        existing = self._get_existing_flow(alias)
        if not existing:
            raise ValidationError(f"Flow {alias} not found")
        self.kcadm.update(f'authentication/flows/{existing["id"]}', flow)
        
    def _configure_required_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Configure required actions in Keycloak."""
        for action in actions:
            alias = action['alias']
            existing = self.kcadm.get(f'authentication/required-actions/{alias}')
            
            if existing:
                self.kcadm.update(f'authentication/required-actions/{alias}', action)
            else:
                self.kcadm.create('authentication/required-actions', action)
                
    def execute(self, config: Dict[str, Any]) -> None:
        """Apply authentication configuration to Keycloak."""
        auth_config = config.get('authentication', {})
        
        # Configure authentication flows
        for flow in auth_config.get('flows', []):
            alias = flow['alias']
            existing = self._get_existing_flow(alias)
            
            if existing:
                self._update_flow(alias, flow)
            else:
                self._create_flow(flow)
                
        # Configure required actions
        if 'requiredActions' in auth_config:
            self._configure_required_actions(auth_config['requiredActions'])
                
    def rollback(self) -> None:
        """Rollback authentication configuration changes."""
        # For now, we don't implement rollback as it could affect running authentication flows
        # In the future, we could store the previous state and restore it
        pass
