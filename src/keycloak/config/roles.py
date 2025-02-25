from .base import KeycloakConfigStep, ValidationError
import json
from typing import Dict, Any, List

class RolesConfigStep(KeycloakConfigStep):
    """Configure Keycloak roles"""
    def __init__(self):
        super().__init__("roles")

    def validate(self, config: dict) -> bool:
        """Validate roles configuration"""
        try:
            roles_config = config.get("realm", {}).get("roles", [])
            
            if not isinstance(roles_config, list):
                raise ValidationError("Roles configuration must be a list")
            
            for role in roles_config:
                if not isinstance(role, dict):
                    raise ValidationError("Each role must be a dictionary")
                
                # Required fields
                required = ["name"]
                for field in required:
                    if field not in role:
                        raise ValidationError(f"Role missing required field: {field}")
                
                # Validate types
                if not isinstance(role.get("name"), str):
                    raise ValidationError("Role name must be a string")
                if "description" in role and not isinstance(role["description"], str):
                    raise ValidationError("Role description must be a string")
                if "composite" in role and not isinstance(role["composite"], bool):
                    raise ValidationError("Role composite flag must be a boolean")
                
                # Validate composite roles
                if role.get("composite"):
                    composites = role.get("composites", [])
                    if not isinstance(composites, list):
                        raise ValidationError("Role composites must be a list")
                    for composite in composites:
                        if "role" not in composite:
                            raise ValidationError("Composite role must have a role name")
            
            return True
        except ValidationError as e:
            self.logger.error(f"Validation failed: {e}")
            return False

    def execute(self, config: dict) -> bool:
        """Configure Keycloak roles"""
        try:
            self._wait_for_keycloak(config)
            self._authenticate(config)

            realm_name = config["realm"]["name"]
            roles_config = config["realm"].get("roles", [])
            
            # Get current roles for rollback
            try:
                current = self._run_kcadm("get", f"realms/{realm_name}/roles")
                current_roles = json.loads(current.stdout)
                self._record_change("roles_update", {"old_roles": current_roles})
            except:
                self._record_change("roles_create", {"realm": realm_name})

            # Create/update roles
            for role in roles_config:
                self._configure_role(realm_name, role)
            
            # Configure default roles if specified
            if "defaultRoles" in config["realm"]:
                self._configure_default_roles(realm_name, config["realm"]["defaultRoles"])
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure roles: {e}")
            return False

    def rollback(self) -> bool:
        """Rollback roles configuration changes"""
        try:
            for change in reversed(self.changes):
                self.logger.info(f"Rolling back change: {change['action']}")
                
                if change["action"] == "roles_create":
                    # Delete all roles except default
                    realm = change["details"]["realm"]
                    roles = json.loads(self._run_kcadm("get", f"realms/{realm}/roles").stdout)
                    for role in roles:
                        if role["name"] not in ["offline_access", "uma_authorization"]:
                            self._run_kcadm("delete", f"roles/{role['id']}")
                
                elif change["action"] == "roles_update":
                    # Restore old roles
                    old_roles = change["details"]["old_roles"]
                    for role in old_roles:
                        self._run_kcadm(
                            "update", f"roles/{role['id']}",
                            "-s", f"name={role['name']}",
                            "-s", f"description={role.get('description', '')}",
                            "-s", f"composite={str(role.get('composite', False)).lower()}"
                        )
                
                elif change["action"] == "role_create":
                    role_name = change["details"]["name"]
                    realm = change["details"]["realm"]
                    self._run_kcadm("delete", f"realms/{realm}/roles/{role_name}")
                
                elif change["action"] == "default_roles":
                    realm = change["details"]["realm"]
                    old_defaults = change["details"]["old_defaults"]
                    self._run_kcadm(
                        "update", f"realms/{realm}",
                        "-s", f"defaultRoles={json.dumps(old_defaults)}"
                    )
            
            return True
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def _configure_role(self, realm: str, role: Dict[str, Any]):
        """Configure a single role"""
        # Create role
        self._run_kcadm(
            "create", f"realms/{realm}/roles",
            "-s", f"name={role['name']}",
            "-s", f"description={role.get('description', '')}",
            "-s", f"composite={str(role.get('composite', False)).lower()}"
        )
        
        self._record_change("role_create", {
            "name": role["name"],
            "realm": realm
        })
        
        # If composite role, configure composites
        if role.get("composite"):
            role_id = json.loads(
                self._run_kcadm("get", f"realms/{realm}/roles/{role['name']}").stdout
            )["id"]
            
            composites = []
            for composite in role.get("composites", []):
                composite_role = json.loads(
                    self._run_kcadm("get", f"realms/{realm}/roles/{composite['role']}").stdout
                )
                composites.append({"id": composite_role["id"], "name": composite_role["name"]})
            
            if composites:
                self._run_kcadm(
                    "update", f"roles/{role_id}/composites",
                    "-s", f"composites={json.dumps(composites)}"
                )

    def _configure_default_roles(self, realm: str, default_roles: List[str]):
        """Configure realm default roles"""
        # Get current default roles for rollback
        current = self._run_kcadm("get", f"realms/{realm}")
        current_config = json.loads(current.stdout)
        
        self._record_change("default_roles", {
            "realm": realm,
            "old_defaults": current_config.get("defaultRoles", [])
        })
        
        # Update default roles
        self._run_kcadm(
            "update", f"realms/{realm}",
            "-s", f"defaultRoles={json.dumps(default_roles)}"
        )
