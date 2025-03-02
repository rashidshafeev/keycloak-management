from .base import KeycloakConfigStep, ValidationError
import json
from typing import Dict, Any

class RealmConfigStep(KeycloakConfigStep):
    """Configure Keycloak realm settings"""
    def __init__(self):
        super().__init__("realm")

    def validate(self, config: dict) -> bool:
        """Validate realm configuration"""
        try:
            realm_config = config.get("realm", {})
            
            # Required fields
            required = ["name", "displayName"]
            for field in required:
                if field not in realm_config:
                    raise ValidationError(f"Realm configuration missing required field: {field}")
            
            # Validate types
            if not isinstance(realm_config.get("ssoSessionIdleTimeout", 1800), int):
                raise ValidationError("ssoSessionIdleTimeout must be an integer")
            if not isinstance(realm_config.get("ssoSessionMaxLifespan", 36000), int):
                raise ValidationError("ssoSessionMaxLifespan must be an integer")
            
            return True
        except ValidationError as e:
            self.logger.error(f"Validation failed: {e}")
            return False

    def execute(self, config: dict) -> bool:
        """Configure Keycloak realm"""
        try:
            self._wait_for_keycloak(config)
            self._authenticate(config)

            realm_config = config.get("realm", {})
            
            # Get current config for rollback if realm exists
            try:
                current = self._run_kcadm("get", f"realms/{realm_config['name']}")
                current_config = json.loads(current.stdout)
                self._record_change("realm_update", {"old_config": current_config})
            except:
                self._record_change("realm_create", {"name": realm_config["name"]})

            # Create or update realm
            self._configure_realm(realm_config)
            
            # Configure security defenses
            self._configure_security(realm_config)
            
            # Configure token settings
            self._configure_tokens(realm_config)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure realm: {e}")
            return False

    def rollback(self) -> bool:
        """Rollback realm configuration changes"""
        try:
            for change in reversed(self.changes):
                self.logger.info(f"Rolling back change: {change['action']}")
                
                if change["action"] == "realm_create":
                    self._run_kcadm("delete", f"realms/{change['details']['name']}")
                
                elif change["action"] == "realm_update":
                    old_config = change["details"]["old_config"]
                    self._run_kcadm(
                        "update", f"realms/{old_config['realm']}",
                        "-s", f"enabled={str(old_config.get('enabled', True)).lower()}",
                        "-s", f"displayName={old_config.get('displayName')}",
                        "-s", f"sslRequired={old_config.get('sslRequired', 'EXTERNAL')}",
                        "-s", f"registrationAllowed={str(old_config.get('registrationAllowed', False)).lower()}",
                        "-s", f"editUsernameAllowed={str(old_config.get('editUsernameAllowed', False)).lower()}",
                        "-s", f"resetPasswordAllowed={str(old_config.get('resetPasswordAllowed', True)).lower()}"
                    )
            
            return True
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def _configure_realm(self, config: Dict[str, Any]):
        """Configure basic realm settings"""
        self._run_kcadm(
            "create", "realms",
            "-s", f"realm={config['name']}",
            "-s", f"enabled={str(config.get('enabled', True)).lower()}",
            "-s", f"displayName={config['displayName']}",
            "-s", f"sslRequired={config.get('sslRequired', 'EXTERNAL')}",
            "-s", f"registrationAllowed={str(config.get('registrationAllowed', False)).lower()}",
            "-s", f"editUsernameAllowed={str(config.get('editUsernameAllowed', False)).lower()}",
            "-s", f"resetPasswordAllowed={str(config.get('resetPasswordAllowed', True)).lower()}"
        )

    def _configure_security(self, config: Dict[str, Any]):
        """Configure realm security settings"""
        security = config.get("security", {})
        self._run_kcadm(
            "update", f"realms/{config['name']}",
            "-s", f"bruteForceProtected={str(security.get('bruteForceProtected', True)).lower()}",
            "-s", f"permanentLockout={str(security.get('permanentLockout', False)).lower()}",
            "-s", f"maxFailureWaitSeconds={security.get('maxFailureWaitSeconds', 900)}",
            "-s", f"minimumQuickLoginWaitSeconds={security.get('minimumQuickLoginWaitSeconds', 60)}",
            "-s", f"waitIncrementSeconds={security.get('waitIncrementSeconds', 60)}",
            "-s", f"quickLoginCheckMilliSeconds={security.get('quickLoginCheckMilliSeconds', 1000)}",
            "-s", f"maxDeltaTimeSeconds={security.get('maxDeltaTimeSeconds', 43200)}"
        )

    def _configure_tokens(self, config: Dict[str, Any]):
        """Configure realm token settings"""
        tokens = config.get("tokens", {})
        self._run_kcadm(
            "update", f"realms/{config['name']}",
            "-s", f"defaultSignatureAlgorithm={tokens.get('defaultSignatureAlgorithm', 'RS256')}",
            "-s", f"revokeRefreshToken={str(tokens.get('revokeRefreshToken', True)).lower()}",
            "-s", f"refreshTokenMaxReuse={tokens.get('refreshTokenMaxReuse', 0)}",
            "-s", f"ssoSessionIdleTimeout={tokens.get('ssoSessionIdleTimeout', 1800)}",
            "-s", f"ssoSessionMaxLifespan={tokens.get('ssoSessionMaxLifespan', 36000)}",
            "-s", f"offlineSessionIdleTimeout={tokens.get('offlineSessionIdleTimeout', 2592000)}",
            "-s", f"accessTokenLifespan={tokens.get('accessTokenLifespan', 300)}",
            "-s", f"accessTokenLifespanForImplicitFlow={tokens.get('accessTokenLifespanForImplicitFlow', 900)}"
        )
