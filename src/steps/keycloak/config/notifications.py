# /keycloak-management/src/keycloak/config/notifications.py
class NotificationConfigurator(BaseConfigurator):
    def configure(self, interactive: bool = False):
        """Configure email and SMS providers"""
        config = self._load_config_file("notifications.json")
        
        # Email configuration
        email_config = config.get("email", {})
        if interactive:
            email_config.update(self._prompt_email_config())
        else:
            email_config.update({
                "host": self._get_env_value("SMTP_HOST", "smtp.gmail.com"),
                "port": self._get_env_value("SMTP_PORT", "587"),
                "from": self._get_env_value("SMTP_FROM"),
                "user": self._get_env_value("SMTP_USER"),
                "password": self._get_env_value("SMTP_PASSWORD")
            })

        # SMS configuration (Twilio example)
        sms_config = config.get("sms", {})
        if interactive:
            sms_config.update(self._prompt_sms_config())
        else:
            sms_config.update({
                "provider": "twilio",
                "account_sid": self._get_env_value("TWILIO_ACCOUNT_SID"),
                "auth_token": self._get_env_value("TWILIO_AUTH_TOKEN"),
                "from_number": self._get_env_value("TWILIO_FROM_NUMBER")
            })

        self._apply_email_config(email_config)
        self._apply_sms_config(sms_config)

    def _prompt_email_config(self) -> dict:
        """Interactive email configuration"""
        return {
            "host": click.prompt("SMTP Host", default="smtp.gmail.com"),
            "port": click.prompt("SMTP Port", default="587"),
            "from": click.prompt("From Email"),
            "user": click.prompt("SMTP Username"),
            "password": click.prompt("SMTP Password", hide_input=True)
        }

    def _prompt_sms_config(self) -> dict:
        """Interactive SMS configuration"""
        return {
            "provider": click.prompt("SMS Provider", default="twilio"),
            "account_sid": click.prompt("Account SID"),
            "auth_token": click.prompt("Auth Token", hide_input=True),
            "from_number": click.prompt("From Number")
        }

    def _apply_email_config(self, config: dict):
        """Apply email configuration to Keycloak"""
        # Implementation using Keycloak API
        response = self._make_request(
            'PUT',
            f'/realms/{self.realm_name}/smtp-settings',
            json={
                "host": config["host"],
                "port": config["port"],
                "from": config["from"],
                "auth": True,
                "ssl": True,
                "starttls": True,
                "user": config["user"],
                "password": config["password"]
            }
        )
        if response.status_code != 204:
            raise KeycloakConfigurationError("Failed to configure email settings")

    def _apply_sms_config(self, config: dict):
        """Apply SMS configuration to Keycloak"""
        # This requires custom SPI implementation for SMS
        # Here's example for setting up SMS authentication
        response = self._make_request(
            'POST',
            f'/realms/{self.realm_name}/authentication/flows',
            json={
                "alias": "sms-authentication",
                "providerId": "basic-flow",
                "description": "SMS Authentication Flow"
            }
        )
        if response.status_code != 201:
            raise KeycloakConfigurationError("Failed to create SMS authentication flow")