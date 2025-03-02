"""
SMTP configuration for Keycloak.
"""

from .base import KeycloakConfigStep
from .validation import ValidationError


class SmtpConfigStep(KeycloakConfigStep):
    """Handles SMTP configuration for Keycloak.
    
    This step manages email settings, including:
    - SMTP server configuration
    - Email templates
    - Test email functionality
    """
    
    def _validate_impl(self, config: dict) -> None:
        """Validate SMTP configuration."""
        smtp = config.get('smtp', {})
        if not isinstance(smtp, dict):
            raise ValidationError("'smtp' must be a dictionary", "smtp")
        
        required_fields = ['host', 'port', 'from']
        for field in required_fields:
            if field not in smtp:
                raise ValidationError(f"Required field '{field}' missing in SMTP configuration", f"smtp.{field}")
        
        if not isinstance(smtp['port'], int):
            raise ValidationError("SMTP port must be an integer", "smtp.port")
    
    def _execute_impl(self, config: dict) -> None:
        """Apply SMTP configuration."""
        smtp = config.get('smtp', {})
        
        # Configure SMTP settings
        cmd_args = [
            'update', 'realms/master',
            '-s', f'smtpServer.host={smtp["host"]}',
            '-s', f'smtpServer.port={smtp["port"]}',
            '-s', f'smtpServer.from={smtp["from"]}',
        ]
        
        # Optional settings
        if 'auth' in smtp:
            cmd_args.extend([
                '-s', f'smtpServer.user={smtp["auth"]["user"]}',
                '-s', f'smtpServer.password={smtp["auth"]["password"]}',
            ])
        
        if 'ssl' in smtp:
            cmd_args.extend(['-s', f'smtpServer.ssl={str(smtp["ssl"]).lower()}'])
        
        if 'starttls' in smtp:
            cmd_args.extend(['-s', f'smtpServer.starttls={str(smtp["starttls"]).lower()}'])
        
        self.run_kcadm_command(*cmd_args)
        
        # Test email configuration if requested
        if smtp.get('test', False):
            self._test_email_config(smtp)
    
    def _rollback_impl(self) -> None:
        """Rollback SMTP configuration changes."""
        # Remove SMTP configuration
        self.run_kcadm_command('update', 'realms/master',
                             '-s', 'smtpServer=null')
    
    def _test_email_config(self, smtp: dict) -> None:
        """Send a test email to verify configuration."""
        test_email = smtp.get('test_email', smtp['from'])
        self.run_kcadm_command('update', 'realms/master',
                             '-s', f'testSmtpConnection=true',
                             '-s', f'testSmtpEmail={test_email}')
