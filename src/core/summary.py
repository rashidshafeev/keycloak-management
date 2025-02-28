"""
Installation summary generator for Keycloak Management System
"""
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class InstallationSummaryGenerator:
    """Generates comprehensive installation summaries"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.template_path = Path(__file__).parent / "installation_summary.md.template"
    
    def _get_service_status(self, services: List[str]) -> List[str]:
        """Get status of specified services"""
        service_status = []
        for service in services:
            try:
                status = subprocess.run(
                    ['systemctl', 'status', service], 
                    capture_output=True,
                    text=True,
                    check=False
                ).stdout
                service_status.append(f"### {service}\n```\n{status}\n```\n")
            except Exception as e:
                service_status.append(f"### {service}\nError getting status: {e}\n")
        return service_status
    
    def _get_ssl_expiry(self, cert_path: str) -> str:
        """Get SSL certificate expiry date"""
        try:
            if not cert_path:
                return "Certificate path not configured"
                
            result = subprocess.run(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path], 
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip() if result.returncode == 0 else "Error reading certificate"
        except Exception as e:
            return f"Error checking SSL expiry: {str(e)}"
    
    def _get_last_backup_info(self, backup_path: Path) -> str:
        """Get information about the last backup"""
        try:
            if not backup_path.exists():
                return "Backup directory not found"
                
            backups = sorted(backup_path.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True)
            if not backups:
                return "No backups found"
                
            return datetime.fromtimestamp(backups[0].stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return f"Error checking backups: {str(e)}"
    
    def generate(self) -> bool:
        """
        Generate installation summary
        
        Returns:
            bool: True if summary was generated successfully, False otherwise
        """
        try:
            if not self.template_path.exists():
                logger.error(f"Template file not found: {self.template_path}")
                return False
            
            # Read template
            with open(self.template_path, 'r') as f:
                template = Template(f.read())
            
            # Get dynamic information
            services = ['keycloak', 'prometheus', 'grafana-server', 'wazuh-manager']
            service_status = self._get_service_status(services)
            
            ssl_expiry = self._get_ssl_expiry(self.config.get('SSL_CERT_PATH', ''))
            
            backup_path = Path(self.config.get('BACKUP_STORAGE_PATH', '/var/backup/keycloak'))
            last_backup = self._get_last_backup_info(backup_path)
            
            # Prepare variables for the template
            variables = {
                'INSTALL_DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'KEYCLOAK_HOST': self.config.get('KEYCLOAK_DOMAIN', 'localhost'),
                'KEYCLOAK_PORT': self.config.get('KEYCLOAK_PORT', '8443'),
                'KEYCLOAK_ADMIN': self.config.get('KEYCLOAK_ADMIN', 'admin'),
                'KEYCLOAK_ADMIN_PASSWORD': self.config.get('KEYCLOAK_ADMIN_PASSWORD', '******'),
                'PROMETHEUS_HOST': 'localhost',
                'PROMETHEUS_DATA_DIR': self.config.get('PROMETHEUS_DATA_DIR', '/var/lib/prometheus'),
                'GRAFANA_HOST': 'localhost',
                'GRAFANA_ADMIN_USER': self.config.get('GRAFANA_ADMIN_USER', 'admin'),
                'GRAFANA_ADMIN_PASSWORD': self.config.get('GRAFANA_ADMIN_PASSWORD', '******'),
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
                'DB_PASSWORD': '******',  # Never show actual password in summary
                'SSL_CERT_PATH': self.config.get('SSL_CERT_PATH', ''),
                'SSL_KEY_PATH': self.config.get('SSL_KEY_PATH', ''),
                'SSL_EXPIRY_DATE': ssl_expiry,
                'INSTALL_ROOT': str(Path(self.config.get('INSTALL_ROOT', '/opt/keycloak'))),
                'CONFIG_DIR': '/etc/keycloak',
                'LOG_DIR': '/var/log/keycloak',
                'BACKUP_STORAGE_PATH': str(backup_path),
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
                
            logger.info(f"Installation summary generated at {summary_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate installation summary: {str(e)}")
            return False