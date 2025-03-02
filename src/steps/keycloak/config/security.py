from pathlib import Path
from typing import Dict, Any, List
from .base import KeycloakConfigStep, ValidationError

class SecurityConfigStep(KeycloakConfigStep):
    """Configure Keycloak security settings"""
    
    def __init__(self, config_dir: Path):
        super().__init__("security", config_dir)
        self.schema_file = "security_schema.json"
        self.required_fields = {"passwordPolicy", "bruteForceProtection", "ssl"}
        self.optional_fields = {"headers", "webAuthn"}

    def _validate_impl(self, config: dict) -> bool:
        """Validate security configuration"""
        security_config = config.get("security", {})
        
        # Validate password policy
        policies = security_config.get("passwordPolicy", [])
        if not isinstance(policies, list):
            raise ValidationError("passwordPolicy must be a list")
            
        valid_policy_types = {
            "length", "digits", "lowerCase", "upperCase", "specialChars",
            "notUsername", "notEmail", "passwordHistory",
            "forceExpiredPasswordChange", "hashIterations"
        }
        
        for policy in policies:
            if not isinstance(policy, dict):
                raise ValidationError("Each password policy must be an object")
            if "type" not in policy or "value" not in policy:
                raise ValidationError("Each password policy must have 'type' and 'value'")
            if policy["type"] not in valid_policy_types:
                raise ValidationError(f"Invalid policy type: {policy['type']}")
        
        # Validate brute force protection
        brute_force = security_config.get("bruteForceProtection", {})
        if not isinstance(brute_force, dict):
            raise ValidationError("bruteForceProtection must be an object")
            
        # Validate SSL settings
        ssl = security_config.get("ssl", {})
        if not isinstance(ssl, dict):
            raise ValidationError("ssl must be an object")
            
        valid_ssl_levels = {"all", "external", "none"}
        if "required" in ssl and ssl["required"] not in valid_ssl_levels:
            raise ValidationError(f"Invalid SSL requirement: {ssl['required']}")
        
        return True

    def _execute_impl(self, config: dict) -> bool:
        """Apply security configuration"""
        security_config = config.get("security", {})
        
        try:
            # Configure password policy
            self._configure_password_policy(security_config.get("passwordPolicy", []))
            
            # Configure brute force protection
            self._configure_brute_force(security_config.get("bruteForceProtection", {}))
            
            # Configure SSL requirements
            self._configure_ssl(security_config.get("ssl", {}))
            
            # Configure security headers
            if "headers" in security_config:
                self._configure_headers(security_config["headers"])
            
            # Configure WebAuthn
            if "webAuthn" in security_config:
                self._configure_webauthn(security_config["webAuthn"])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply security configuration: {str(e)}")
            return False

    def _rollback_impl(self) -> bool:
        """Rollback security configuration changes"""
        try:
            for change in reversed(self.changes):
                command = change.get("command")
                args = change.get("args", [])
                if command:
                    self.run_kcadm_command(command, *args)
            return True
        except Exception as e:
            self.logger.error(f"Failed to rollback security changes: {str(e)}")
            return False

    def _configure_password_policy(self, policies: List[Dict[str, Any]]):
        """Configure password policies"""
        policy_str = " and ".join(
            f"{p['type']}({p['value']})" for p in policies
        )
        
        self.changes.append({
            "command": "update",
            "args": [
                "realms/master",
                "-s", f"passwordPolicy='{policy_str}'"
            ]
        })
        
        self.run_kcadm_command(
            "update",
            "realms/master",
            "-s", f"passwordPolicy='{policy_str}'"
        )

    def _configure_brute_force(self, config: Dict[str, Any]):
        """Configure brute force protection"""
        args = []
        for key, value in config.items():
            if key == "enabled":
                args.extend(["-s", f"bruteForceProtected={str(value).lower()}"])
            elif key == "maxLoginFailures":
                args.extend(["-s", f"failureFactor={value}"])
            elif key == "waitIncrements":
                args.extend(["-s", f"waitIncrementSeconds={value}"])
            elif key == "quickLoginCheckMillis":
                args.extend(["-s", f"quickLoginCheckMilliSeconds={value}"])
            elif key == "minimumQuickLoginWaitSeconds":
                args.extend(["-s", f"minimumQuickLoginWaitSeconds={value}"])
            elif key == "maxFailureWaitSeconds":
                args.extend(["-s", f"maxFailureWaitSeconds={value}"])
            elif key == "failureResetTimeSeconds":
                args.extend(["-s", f"failureResetTimeSeconds={value}"])
        
        if args:
            self.changes.append({
                "command": "update",
                "args": ["realms/master"] + args
            })
            
            self.run_kcadm_command("update", "realms/master", *args)

    def _configure_ssl(self, config: Dict[str, Any]):
        """Configure SSL requirements"""
        args = []
        
        if "required" in config:
            args.extend(["-s", f"sslRequired={config['required']}"])
        
        if "hostnameVerification" in config:
            args.extend([
                "-s",
                f"hostnameVerificationPolicy={'VERIFY' if config['hostnameVerification'] else 'ANY'}"
            ])
        
        if args:
            self.changes.append({
                "command": "update",
                "args": ["realms/master"] + args
            })
            
            self.run_kcadm_command("update", "realms/master", *args)

    def _configure_headers(self, config: Dict[str, Any]):
        """Configure security headers"""
        args = []
        
        header_mapping = {
            "xFrameOptions": "xFrameOptions",
            "contentSecurityPolicy": "contentSecurityPolicy",
            "xContentTypeOptions": "xContentTypeOptions",
            "xRobotsTag": "xRobotsTag",
            "xXSSProtection": "xXSSProtection"
        }
        
        for yaml_key, header_key in header_mapping.items():
            if yaml_key in config:
                args.extend(["-s", f"browserSecurityHeaders.{header_key}={config[yaml_key]}"])
        
        if args:
            self.changes.append({
                "command": "update",
                "args": ["realms/master"] + args
            })
            
            self.run_kcadm_command("update", "realms/master", *args)

    def _configure_webauthn(self, config: Dict[str, Any]):
        """Configure WebAuthn settings"""
        args = []
        
        if "enabled" in config:
            args.extend(["-s", f"webAuthnPolicyEnabled={str(config['enabled']).lower()}"])
        
        if "passwordless" in config:
            args.extend(["-s", f"webAuthnPolicyPasswordlessEnabled={str(config['passwordless']).lower()}"])
        
        webauthn_mapping = {
            "attestationConveyancePreference": "webAuthnPolicyAttestationConveyancePreference",
            "authenticatorAttachment": "webAuthnPolicyAuthenticatorAttachment",
            "requireResidentKey": "webAuthnPolicyRequireResidentKey",
            "userVerificationRequirement": "webAuthnPolicyUserVerificationRequirement",
            "signatureAlgorithms": "webAuthnPolicySignatureAlgorithms"
        }
        
        for yaml_key, policy_key in webauthn_mapping.items():
            if yaml_key in config:
                value = config[yaml_key]
                if isinstance(value, list):
                    value = "[" + ",".join(value) + "]"
                args.extend(["-s", f"{policy_key}={value}"])
        
        if args:
            self.changes.append({
                "command": "update",
                "args": ["realms/master"] + args
            })
            
            self.run_kcadm_command("update", "realms/master", *args)
