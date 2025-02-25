from ..deployment.base import DeploymentStep
import subprocess
from pathlib import Path
import logging
import yaml
from typing import Dict, List, Optional
import shutil
from datetime import datetime
import os
import time
import requests
import json
from string import Template

class PrometheusManager(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("prometheus_management", can_cleanup=False)
        self.config = config
        self.prom_dir = Path("/etc/prometheus")
        self.grafana_dir = Path("/etc/grafana")
        self.backup_dir = Path("/opt/fawz/keycloak/monitoring/backup")
        self.dashboard_dir = Path("/opt/fawz/keycloak/monitoring/dashboards")
        
        # Get config file paths
        module_dir = Path(__file__).parent
        self.config_dir = module_dir / "config"
        
        # Default configuration
        self.prom_config = {
            'PROMETHEUS_SCRAPE_INTERVAL': '15s',
            'PROMETHEUS_EVAL_INTERVAL': '15s',
            'PROMETHEUS_RETENTION_TIME': '15d'
        }
        
        # Update with user config if provided
        if 'prometheus' in self.config:
            self.prom_config.update(self.config['prometheus'])

    def _apply_template(self, template_path: Path, output_path: Path, variables: Dict[str, str]):
        """Apply template with variables"""
        with open(template_path, 'r') as f:
            template = Template(f.read())
        
        content = template.safe_substitute(variables)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)

    def _backup_config(self) -> Optional[Path]:
        """Backup Prometheus and Grafana configurations"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup Prometheus config
            if self.prom_dir.exists():
                shutil.copytree(
                    self.prom_dir,
                    backup_path / "prometheus",
                    dirs_exist_ok=True
                )

            # Backup Grafana config
            if self.grafana_dir.exists():
                shutil.copytree(
                    self.grafana_dir,
                    backup_path / "grafana",
                    dirs_exist_ok=True
                )

            self.logger.info(f"Created monitoring backup at {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None

    def _restore_backup(self, backup_path: Optional[Path] = None) -> bool:
        """Restore monitoring configuration from backup"""
        try:
            if not backup_path:
                backups = sorted(self.backup_dir.glob('*'), reverse=True)
                if not backups:
                    return False
                backup_path = backups[0]

            # Restore Prometheus config
            prom_backup = backup_path / "prometheus"
            if prom_backup.exists():
                shutil.copytree(
                    prom_backup,
                    self.prom_dir,
                    dirs_exist_ok=True
                )

            # Restore Grafana config
            grafana_backup = backup_path / "grafana"
            if grafana_backup.exists():
                shutil.copytree(
                    grafana_backup,
                    self.grafana_dir,
                    dirs_exist_ok=True
                )

            # Restart services
            subprocess.run(["systemctl", "restart", "prometheus"], check=True)
            subprocess.run(["systemctl", "restart", "grafana-server"], check=True)

            self.logger.info(f"Restored monitoring from {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False

    def _install_prometheus(self) -> bool:
        """Install Prometheus and node_exporter"""
        try:
            # Install packages
            subprocess.run([
                "apt-get", "install", "-y",
                "prometheus",
                "prometheus-node-exporter",
                "prometheus-jmx-exporter"
            ], check=True)

            # Copy configuration files
            prom_config_dir = self.config_dir / "prometheus"
            
            # Copy and apply main config
            self._apply_template(
                prom_config_dir / "prometheus.yml",
                self.prom_dir / "prometheus.yml",
                self.prom_config
            )
            
            # Copy scrape configs
            shutil.copy2(
                prom_config_dir / "scrape_configs.yml",
                self.prom_dir / "scrape_configs.yml"
            )
            
            # Copy alert rules
            alerts_dir = self.prom_dir / "alerts"
            alerts_dir.mkdir(parents=True, exist_ok=True)
            
            for alert_file in (prom_config_dir / "alerts").glob("*.yml"):
                shutil.copy2(alert_file, alerts_dir / alert_file.name)

            # Configure Docker metrics
            docker_config = {
                'metrics-addr': 'localhost:9323',
                'experimental': True
            }
            docker_daemon_file = Path("/etc/docker/daemon.json")
            if not docker_daemon_file.exists():
                docker_daemon_file.parent.mkdir(parents=True, exist_ok=True)
                with open(docker_daemon_file, 'w') as f:
                    json.dump(docker_config, f)

            # Restart Docker to apply metrics configuration
            subprocess.run(["systemctl", "restart", "docker"], check=True)

            # Start Prometheus
            subprocess.run(["systemctl", "enable", "prometheus"], check=True)
            subprocess.run(["systemctl", "restart", "prometheus"], check=True)

            return True
        except Exception as e:
            self.logger.error(f"Prometheus installation failed: {e}")
            return False

    def _install_grafana(self) -> bool:
        """Install and configure Grafana"""
        try:
            # Install Grafana
            subprocess.run([
                "apt-get", "install", "-y", "grafana"
            ], check=True)

            # Prepare variables for templates
            grafana_vars = {
                'GRAFANA_ADMIN_USER': self.config.get('grafana', {}).get('admin_user', 'admin'),
                'GRAFANA_ADMIN_PASSWORD': self.config.get('grafana', {}).get('admin_password', 'admin'),
                'GRAFANA_SMTP_HOST': self.config.get('grafana', {}).get('smtp_host', ''),
                'GRAFANA_SMTP_USER': self.config.get('grafana', {}).get('smtp_user', ''),
                'GRAFANA_SMTP_PASSWORD': self.config.get('grafana', {}).get('smtp_password', ''),
                'GRAFANA_SMTP_FROM': self.config.get('grafana', {}).get('smtp_from', ''),
                'GRAFANA_ALERT_EMAIL': self.config.get('grafana', {}).get('alert_email', ''),
                'GRAFANA_SLACK_WEBHOOK_URL': self.config.get('grafana', {}).get('slack_webhook_url', ''),
                'GRAFANA_SLACK_CHANNEL': self.config.get('grafana', {}).get('slack_channel', '#alerts')
            }

            grafana_config_dir = self.config_dir / "grafana"

            # Apply Grafana config
            self._apply_template(
                grafana_config_dir / "grafana.ini",
                self.grafana_dir / "grafana.ini",
                grafana_vars
            )

            # Start Grafana
            subprocess.run(["systemctl", "enable", "grafana-server"], check=True)
            subprocess.run(["systemctl", "restart", "grafana-server"], check=True)

            # Wait for Grafana to start
            self._wait_for_grafana()

            # Configure datasource
            self._configure_grafana_datasource()

            # Configure notification channels
            self._configure_grafana_notifications()

            # Import dashboards
            self._import_dashboards()

            return True
        except Exception as e:
            self.logger.error(f"Grafana installation failed: {e}")
            return False

    def _wait_for_grafana(self, timeout: int = 60):
        """Wait for Grafana to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:3000/api/health")
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        raise TimeoutError("Grafana failed to start")

    def _configure_grafana_datasource(self):
        """Configure Prometheus datasource in Grafana"""
        datasource = {
            'name': 'Prometheus',
            'type': 'prometheus',
            'url': 'http://localhost:9090',
            'access': 'proxy',
            'isDefault': True
        }

        auth = (
            self.config.get('grafana', {}).get('admin_user', 'admin'),
            self.config.get('grafana', {}).get('admin_password', 'admin')
        )

        response = requests.post(
            'http://localhost:3000/api/datasources',
            json=datasource,
            auth=auth
        )
        response.raise_for_status()

    def _configure_grafana_notifications(self):
        """Configure Grafana notification channels"""
        grafana_config_dir = self.config_dir / "grafana"
        with open(grafana_config_dir / "notifications.yml", 'r') as f:
            notification_channels = yaml.safe_load(f)

        auth = (
            self.config.get('grafana', {}).get('admin_user', 'admin'),
            self.config.get('grafana', {}).get('admin_password', 'admin')
        )

        for channel in notification_channels:
            if channel['type'] == 'email' and not channel['settings']['addresses']:
                continue
            if channel['type'] == 'slack' and not channel['settings']['url']:
                continue

            response = requests.post(
                'http://localhost:3000/api/alert-notifications',
                json=channel,
                auth=auth
            )
            response.raise_for_status()

    def _import_dashboards(self):
        """Import all monitoring dashboards"""
        grafana_config_dir = self.config_dir / "grafana"
        dashboard_dir = grafana_config_dir / "dashboards"

        auth = (
            self.config.get('grafana', {}).get('admin_user', 'admin'),
            self.config.get('grafana', {}).get('admin_password', 'admin')
        )

        for dashboard_file in dashboard_dir.glob("*.json"):
            with open(dashboard_file, 'r') as f:
                dashboard = json.load(f)
                response = requests.post(
                    'http://localhost:3000/api/dashboards/db',
                    json={'dashboard': dashboard['dashboard'], 'overwrite': True},
                    auth=auth
                )
                response.raise_for_status()

    def check_completed(self) -> bool:
        """Check if monitoring is properly configured"""
        try:
            # Check if Prometheus is running
            result = subprocess.run(
                ["systemctl", "is-active", "prometheus"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False

            # Check if Grafana is running
            result = subprocess.run(
                ["systemctl", "is-active", "grafana-server"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False

            # Check if dashboards are configured
            try:
                auth = (
                    self.config.get('grafana', {}).get('admin_user', 'admin'),
                    self.config.get('grafana', {}).get('admin_password', 'admin')
                )
                response = requests.get(
                    'http://localhost:3000/api/dashboards/uid/keycloak-overview',
                    auth=auth
                )
                if response.status_code != 200:
                    return False
            except:
                return False

            return True
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return False

    def execute(self) -> bool:
        """Install and configure monitoring"""
        try:
            if self.check_completed():
                self.logger.info("Monitoring already properly configured")
                return True

            # Create backup before making changes
            backup_path = self._backup_config()

            # Install and configure Prometheus
            if not self._install_prometheus():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Install and configure Grafana
            if not self._install_grafana():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            self.logger.info("Monitoring configuration completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Monitoring configuration failed: {e}")
            if backup_path:
                self._restore_backup(backup_path)
            return False
