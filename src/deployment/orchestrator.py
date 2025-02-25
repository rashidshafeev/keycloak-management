import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, ContextManager
from contextlib import contextmanager
from ..utils.logger import setup_logging
from ..system.prepare import SystemPreparationStep
from ..system.docker import DockerSetupStep
from ..security.ssl import CertificateManager
from ..monitoring.prometheus import PrometheusManager
from ..keycloak.deploy import KeycloakDeploymentStep
from ..keycloak.config.configuration import KeycloakConfigurationManager
from .database_backup import DatabaseBackupStep
from .base import DeploymentStep

class DeploymentOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        """Initialize orchestrator with configuration
        
        Args:
            config: Dictionary containing environment configuration
        """
        self.config = config
        self.logger = logging.getLogger("keycloak_deployer")
        self.steps = [
            SystemPreparationStep(),
            DockerSetupStep(),
            CertificateManager(self.config),
            KeycloakDeploymentStep(self.config),
            KeycloakConfigurationManager(self.config),
            PrometheusManager(self.config),
            DatabaseBackupStep(self.config)
        ]

    @contextmanager
    def step_context(self, step: DeploymentStep):
        try:
            yield
        except Exception as e:
            self.logger.error(f"Step {step.name} failed: {e}")
            if step.can_cleanup:
                step.cleanup()
            raise

    def _generate_installation_summary(self) -> None:
        """Generate installation summary with all necessary access information"""
        from datetime import datetime
        import subprocess
        from string import Template
        
        # Get template
        template_path = Path(__file__).parent.parent / "templates" / "installation_summary.md.template"
        with open(template_path, 'r') as f:
            template = Template(f.read())
            
        # Collect service status
        services = ['keycloak', 'prometheus', 'grafana-server', 'wazuh-manager']
        service_status = []
        for service in services:
            try:
                status = subprocess.run(['systemctl', 'status', service], 
                                     capture_output=True, text=True).stdout
                service_status.append(f"### {service}\n```\n{status}\n```\n")
            except Exception as e:
                service_status.append(f"### {service}\nError getting status: {e}\n")
        
        # Get SSL certificate expiry
        try:
            ssl_expiry = subprocess.run(
                ['openssl', 'x509', '-enddate', '-noout', '-in', self.config['SSL_CERT_PATH']], 
                capture_output=True, text=True
            ).stdout.strip()
        except:
            ssl_expiry = "Unknown"
            
        # Get last backup date
        try:
            backup_path = Path(self.config.get('BACKUP_STORAGE_PATH', '/var/backup/keycloak'))
            backups = sorted(backup_path.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
            last_backup = datetime.fromtimestamp(backups[0].stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if backups else "No backups found"
        except:
            last_backup = "Unknown"
            
        # Prepare variables
        variables = {
            'INSTALL_DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'KEYCLOAK_HOST': self.config['KEYCLOAK_DOMAIN'],
            'KEYCLOAK_PORT': self.config.get('KEYCLOAK_PORT', '8443'),
            'KEYCLOAK_ADMIN': self.config['KEYCLOAK_ADMIN'],
            'KEYCLOAK_ADMIN_PASSWORD': self.config['KEYCLOAK_ADMIN_PASSWORD'],
            'PROMETHEUS_HOST': 'localhost',
            'PROMETHEUS_DATA_DIR': self.config.get('PROMETHEUS_DATA_DIR', '/var/lib/prometheus'),
            'GRAFANA_HOST': 'localhost',
            'GRAFANA_ADMIN_USER': self.config.get('GRAFANA_ADMIN_USER', 'admin'),
            'GRAFANA_ADMIN_PASSWORD': self.config.get('GRAFANA_ADMIN_PASSWORD', 'admin'),
            'GRAFANA_ALERT_EMAIL': self.config.get('GRAFANA_ALERT_EMAIL', ''),
            'GRAFANA_SLACK_CHANNEL': self.config.get('GRAFANA_SLACK_CHANNEL', '#alerts'),
            'WAZUH_MANAGER_IP': self.config.get('WAZUH_MANAGER_IP', 'localhost'),
            'WAZUH_AGENT_NAME': self.config.get('WAZUH_AGENT_NAME', 'keycloak-agent'),
            'WAZUH_AGENT_ID': 'Run "wazuh-agent -l" to get ID',
            'FIREWALL_ALLOWED_PORTS': self.config.get('FIREWALL_ALLOWED_PORTS', '80,443,8080,8443'),
            'FIREWALL_ADMIN_IPS': self.config.get('FIREWALL_ADMIN_IPS', '127.0.0.1'),
            'DB_HOST': self.config.get('DB_HOST', 'localhost'),
            'DB_PORT': self.config.get('DB_PORT', '5432'),
            'DB_NAME': self.config.get('DB_NAME', 'keycloak'),
            'DB_USER': self.config.get('DB_USER', 'keycloak'),
            'DB_PASSWORD': self.config['DB_PASSWORD'],
            'SSL_CERT_PATH': self.config.get('SSL_CERT_PATH', ''),
            'SSL_KEY_PATH': self.config.get('SSL_KEY_PATH', ''),
            'SSL_EXPIRY_DATE': ssl_expiry,
            'INSTALL_ROOT': str(Path(__file__).parent.parent.parent),
            'CONFIG_DIR': '/etc/keycloak',
            'LOG_DIR': '/var/log/keycloak',
            'BACKUP_STORAGE_PATH': self.config.get('BACKUP_STORAGE_PATH', '/var/backup/keycloak'),
            'DOCKER_VOLUMES_PATH': '/var/lib/docker/volumes',
            'SERVICE_STATUS': '\n'.join(service_status),
            'BACKUP_TIME': self.config.get('BACKUP_TIME', '02:00'),
            'BACKUP_RETENTION_DAYS': self.config.get('BACKUP_RETENTION_DAYS', '30'),
            'LAST_BACKUP_DATE': last_backup,
            'DEBUG_MODE': str(self.config.get('DEBUG_MODE', False)),
            'SUPPORT_EMAIL': self.config.get('SUPPORT_EMAIL', 'support@example.com'),
            'ADDITIONAL_NOTES': self.config.get('ADDITIONAL_NOTES', 'No additional notes.')
        }
        
        # Generate summary
        summary = template.safe_substitute(variables)
        
        # Save summary
        summary_path = Path(self.config.get('INSTALL_ROOT', '/opt/keycloak')) / 'installation_summary.md'
        with open(summary_path, 'w') as f:
            f.write(summary)
            
        self.logger.info(f"Installation summary generated at {summary_path}")

    def deploy(self) -> bool:
        """Deploy Keycloak with all components"""
        for step in self.steps:
            if step.can_skip and step.check_completed():
                self.logger.info(f"Step {step.name} already completed, skipping...")
                continue

            self.logger.info(f"Executing step: {step.name}")
            with self.step_context(step):
                if not step.execute():
                    return False

        self._generate_installation_summary()
        return True
