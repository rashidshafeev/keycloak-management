from .base import KeycloakConfigStep, ValidationError
import json
from typing import List, Dict, Any

class EventConfigStep(KeycloakConfigStep):
    """Configure Keycloak events and listeners"""
    
    # Valid event types
    VALID_EVENTS = {
        # Authentication Events
        "LOGIN", "LOGIN_ERROR", "LOGOUT", "LOGOUT_ERROR",
        # Registration Events
        "REGISTER", "REGISTER_ERROR", "UPDATE_PROFILE",
        "UPDATE_PASSWORD", "UPDATE_EMAIL", "VERIFY_EMAIL",
        # Session Events
        "CODE_TO_TOKEN", "REFRESH_TOKEN", "TOKEN_EXCHANGE", "REMOVE_TOKEN",
        # Client Events
        "CLIENT_LOGIN", "CLIENT_INITIATED_ACCOUNT_LINKING",
        # Identity Provider Events
        "IDENTITY_PROVIDER_LOGIN", "IDENTITY_PROVIDER_LINK_ACCOUNT"
    }
    
    def __init__(self):
        super().__init__("events")

    def validate(self, config: dict) -> bool:
        """Validate event configuration"""
        try:
            events_config = config.get("events", {})
            
            # Validate event storage
            storage = events_config.get("storage", {})
            if not isinstance(storage.get("expiration"), int):
                raise ValidationError("Event storage expiration must be an integer")
            
            # Validate event listeners
            listeners = events_config.get("listeners", [])
            if not isinstance(listeners, list):
                raise ValidationError("Event listeners must be a list")
            
            for listener in listeners:
                if not isinstance(listener, dict):
                    raise ValidationError("Each listener must be a dictionary")
                if "name" not in listener:
                    raise ValidationError("Each listener must have a name")
                if not isinstance(listener.get("enabled"), bool):
                    raise ValidationError("Listener enabled flag must be boolean")
                
                # Validate webhook listener
                if listener.get("type") == "webhook":
                    props = listener.get("properties", {})
                    if "url" not in props:
                        raise ValidationError("Webhook listener must have a URL")
                    if "secret" not in props:
                        raise ValidationError("Webhook listener must have a secret")
                    if "retries" in props and not isinstance(props["retries"], int):
                        raise ValidationError("Webhook retries must be an integer")
                    if "timeout" in props and not isinstance(props["timeout"], int):
                        raise ValidationError("Webhook timeout must be an integer")
            
            # Validate included events
            included_events = events_config.get("included_events", [])
            if not isinstance(included_events, list):
                raise ValidationError("Included events must be a list")
            
            invalid_events = set(included_events) - self.VALID_EVENTS
            if invalid_events:
                raise ValidationError(f"Invalid event types: {invalid_events}")
            
            # Validate admin events
            admin_events = events_config.get("admin_events", {})
            if not isinstance(admin_events.get("enabled", True), bool):
                raise ValidationError("Admin events enabled flag must be boolean")
            if not isinstance(admin_events.get("include_representation", False), bool):
                raise ValidationError("Include representation flag must be boolean")
            
            return True
        except ValidationError as e:
            self.logger.error(f"Validation failed: {e}")
            return False

    def execute(self, config: dict) -> bool:
        """Configure Keycloak events"""
        try:
            self._wait_for_keycloak(config)
            self._authenticate(config)

            realm_name = config["realm"]["name"]
            events_config = config.get("events", {})

            # Configure event storage
            self._configure_event_storage(config)
            
            # Configure event listeners
            self._configure_event_listeners(config)
            
            # Configure included events
            included_events = events_config.get("included_events", [])
            self._run_kcadm(
                "update", f"realms/{realm_name}",
                "-s", f"eventsEnabled=true",
                "-s", f"enabledEventTypes={json.dumps(included_events)}"
            )
            
            # Configure admin events
            admin_events = events_config.get("admin_events", {})
            self._run_kcadm(
                "update", f"realms/{realm_name}",
                "-s", f"adminEventsEnabled={str(admin_events.get('enabled', True)).lower()}",
                "-s", f"adminEventsDetailsEnabled={str(admin_events.get('include_representation', False)).lower()}"
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure events: {e}")
            return False

    def _configure_event_storage(self, config: dict):
        """Configure event storage settings"""
        realm_name = config["realm"]["name"]
        storage = config.get("events", {}).get("storage", {})
        
        self._run_kcadm(
            "update", f"realms/{realm_name}",
            "-s", f"eventsExpiration={storage.get('expiration', 2592000)}"  # 30 days default
        )

    def _configure_event_listeners(self, config: dict):
        """Configure event listeners"""
        realm_name = config["realm"]["name"]
        listeners = config.get("events", {}).get("listeners", [])
        
        # Get current listeners for rollback
        current = self._run_kcadm("get", f"realms/{realm_name}")
        current_config = json.loads(current.stdout)
        self._record_change("event_listeners", {
            "realm": realm_name,
            "old_listeners": current_config.get("eventsListeners", [])
        })
        
        # Configure new listeners
        enabled_listeners = []
        for listener in listeners:
            if listener.get("enabled", True):
                enabled_listeners.append(listener["name"])
                
                # Configure webhook listener if needed
                if listener.get("type") == "webhook":
                    self._configure_webhook_listener(realm_name, listener)
        
        self._run_kcadm(
            "update", f"realms/{realm_name}",
            "-s", f"eventsListeners={json.dumps(enabled_listeners)}"
        )

    def _configure_webhook_listener(self, realm: str, listener: Dict[str, Any]):
        """Configure webhook event listener"""
        props = listener.get("properties", {})
        self._run_kcadm(
            "create", f"realms/{realm}/events/config",
            "-s", f"name={listener['name']}",
            "-s", f"type=webhook",
            "-s", f"config.url={props['url']}",
            "-s", f"config.secret={props['secret']}",
            "-s", f"config.retries={props.get('retries', 3)}",
            "-s", f"config.timeout={props.get('timeout', 5000)}"
        )

    def rollback(self) -> bool:
        """Rollback event configuration changes"""
        try:
            for change in reversed(self.changes):
                self.logger.info(f"Rolling back change: {change['action']}")
                
                if change["action"] == "event_listeners":
                    realm = change["details"]["realm"]
                    old_listeners = change["details"]["old_listeners"]
                    
                    self._run_kcadm(
                        "update", f"realms/{realm}",
                        "-s", f"eventsListeners={json.dumps(old_listeners)}"
                    )
            
            return True
        except Exception as e:
            self.logger.error(f"Event rollback failed: {e}")
            return False
