from pathlib import Path
import logging
from ..utils.logger import setup_logging
from ..system.prepare import SystemPreparationStep
from ..system.docker import DockerSetupStep
from ..system.firewall import FirewallManager
from ..security.ssl import CertificateManager
from ..monitoring.prometheus import PrometheusManager
from ..keycloak.deploy import KeycloakDeploymentStep
from ..keycloak.config.configuration import KeycloakConfigurationManager  # Fixed class name
from .database_backup import DatabaseBackupStep
from .base import DeploymentStep
import json

class DeploymentOrchestrator:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger("keycloak_deployer")
        self.steps = [
            SystemPreparationStep(),
            FirewallManager(self.config),
            DockerSetupStep(),
            CertificateManager(self.config),
            KeycloakDeploymentStep(self.config),
            KeycloakConfigurationManager(self.config),
            PrometheusManager(self.config),
            DatabaseBackupStep(self.config)
        ]

    def _load_config(self, config_path: Path) -> dict:
        return json.loads(config_path.read_text())

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
                ['openssl', 'x509', '-enddate', '-noout', '-in', self.config['ssl']['cert_path']], 
                capture_output=True, text=True
            ).stdout.strip()
        except:
            ssl_expiry = "Unknown"
            
        # Get last backup date
        try:
            backup_path = Path(self.config['backup']['storage_path'])
            backups = sorted(backup_path.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
            last_backup = datetime.fromtimestamp(backups[0].stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if backups else "No backups found"
        except:
            last_backup = "Unknown"
            
        # Prepare variables
        variables = {
            'INSTALL_DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'KEYCLOAK_HOST': self.config['keycloak']['host'],
            'KEYCLOAK_PORT': self.config['keycloak']['port'],
            'KEYCLOAK_ADMIN': self.config['keycloak']['admin_user'],
            'KEYCLOAK_ADMIN_PASSWORD': self.config['keycloak']['admin_password'],
            'PROMETHEUS_HOST': 'localhost',
            'PROMETHEUS_DATA_DIR': '/var/lib/prometheus',
            'GRAFANA_HOST': 'localhost',
            'GRAFANA_ADMIN_USER': self.config['grafana']['admin_user'],
            'GRAFANA_ADMIN_PASSWORD': self.config['grafana']['admin_password'],
            'GRAFANA_ALERT_EMAIL': self.config['grafana'].get('alert_email', ''),
            'GRAFANA_SLACK_CHANNEL': self.config['grafana'].get('slack_channel', '#alerts'),
            'WAZUH_MANAGER_IP': self.config['wazuh']['manager_ip'],
            'WAZUH_AGENT_NAME': self.config['wazuh']['agent_name'],
            'WAZUH_AGENT_ID': 'Run "wazuh-agent -l" to get ID',
            'FIREWALL_ALLOWED_PORTS': ', '.join(map(str, self.config['firewall']['allowed_ports'])),
            'FIREWALL_ADMIN_IPS': ', '.join(self.config['firewall']['admin_ips']),
            'DB_HOST': self.config['database']['host'],
            'DB_PORT': self.config['database']['port'],
            'DB_NAME': self.config['database']['name'],
            'DB_USER': self.config['database']['user'],
            'DB_PASSWORD': self.config['database']['password'],
            'SSL_CERT_PATH': self.config['ssl']['cert_path'],
            'SSL_KEY_PATH': self.config['ssl']['key_path'],
            'SSL_EXPIRY_DATE': ssl_expiry,
            'INSTALL_ROOT': str(Path(__file__).parent.parent.parent),
            'CONFIG_DIR': '/etc/fawz/keycloak',
            'LOG_DIR': '/var/log/fawz/keycloak',
            'BACKUP_STORAGE_PATH': self.config['backup']['storage_path'],
            'DOCKER_VOLUMES_PATH': '/var/lib/docker/volumes',
            'SERVICE_STATUS': '\n'.join(service_status),
            'BACKUP_TIME': self.config['backup'].get('time', '02:00'),
            'BACKUP_RETENTION_DAYS': self.config['backup'].get('retention_days', 30),
            'LAST_BACKUP_DATE': last_backup,
            'DEBUG_MODE': str(self.config.get('debug', False)),
            'SUPPORT_EMAIL': self.config.get('support_email', 'support@example.com'),
            'ADDITIONAL_NOTES': self.config.get('additional_notes', 'No additional notes.')
        }
        
        # Generate summary
        summary = template.safe_substitute(variables)
        
        # Save summary
        summary_path = Path(self.config['install_root']) / 'installation_summary.md'
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
