from ...core.base import BaseStep
import os
import subprocess
import json
import yaml
import shutil
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import step-specific modules
from .dependencies import check_grafana_step_dependencies, install_grafana_step_dependencies
from .environment import get_required_variables, validate_variables

class GrafanaStep(BaseStep):
    """Step for Grafana dashboard and visualization setup"""
    
    def __init__(self):
        super().__init__("grafana_step", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_grafana_step_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_grafana_step_dependencies()
    
    def _backup_config(self, grafana_dir: Path, backup_dir: Path) -> Optional[Path]:
        """Backup Grafana configuration"""
        try:
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup Grafana config if it exists
            if grafana_dir.exists():
                shutil.copytree(
                    grafana_dir,
                    backup_path,
                    dirs_exist_ok=True
                )
                self.logger.info(f"Created Grafana backup at {backup_path}")
                
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
            
    def _restore_backup(self, backup_path: Path, grafana_dir: Path) -> bool:
        """Restore Grafana configuration from backup"""
        try:
            if backup_path.exists():
                # Remove current config
                if grafana_dir.exists():
                    shutil.rmtree(grafana_dir)
                
                # Restore from backup
                shutil.copytree(
                    backup_path,
                    grafana_dir,
                    dirs_exist_ok=True
                )
                
                # Restart Grafana
                subprocess.run(["systemctl", "restart", "grafana-server"], check=False)
                
                self.logger.info(f"Restored Grafana configuration from {backup_path}")
                return True
            else:
                self.logger.error(f"Backup path {backup_path} doesn't exist")
                return False
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def _apply_template(self, template_path: Path, output_path: Path, variables: Dict[str, str]):
        """Apply template with variables"""
        from string import Template
        
        with open(template_path, 'r') as f:
            template = Template(f.read())
        
        content = template.safe_substitute(variables)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
    
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
    
    def _configure_grafana_datasource(self, auth: Tuple[str, str]):
        """Configure Prometheus datasource in Grafana"""
        datasource = {
            'name': 'Prometheus',
            'type': 'prometheus',
            'url': 'http://localhost:9090',
            'access': 'proxy',
            'isDefault': True
        }
        
        response = requests.post(
            'http://localhost:3000/api/datasources',
            json=datasource,
            auth=auth
        )
        response.raise_for_status()
    
    def _configure_grafana_notifications(self, config_dir: Path, auth: Tuple[str, str], env_vars: Dict[str, str]):
        """Configure Grafana notification channels"""
        notifications_file = config_dir / "notifications.yml"
        
        if not notifications_file.exists():
            self.logger.warning(f"Notifications file not found at {notifications_file}")
            return
            
        with open(notifications_file, 'r') as f:
            notification_channels = yaml.safe_load(f)
        
        for channel in notification_channels:
            if channel['type'] == 'email':
                # Configure email notifications
                if env_vars.get('GRAFANA_SMTP_HOST') and env_vars.get('GRAFANA_ALERT_EMAIL'):
                    channel['settings']['addresses'] = env_vars.get('GRAFANA_ALERT_EMAIL')
                else:
                    continue  # Skip if email not configured
                    
            elif channel['type'] == 'slack':
                # Configure Slack notifications
                if env_vars.get('GRAFANA_SLACK_WEBHOOK_URL'):
                    channel['settings']['url'] = env_vars.get('GRAFANA_SLACK_WEBHOOK_URL')
                    channel['settings']['recipient'] = env_vars.get('GRAFANA_SLACK_CHANNEL', '#alerts')
                else:
                    continue  # Skip if Slack not configured
            
            # Create notification channel
            response = requests.post(
                'http://localhost:3000/api/alert-notifications',
                json=channel,
                auth=auth
            )
            
            # Ignore if the notification channel already exists
            if response.status_code == 409:
                self.logger.info(f"Notification channel '{channel['name']}' already exists")
            else:
                response.raise_for_status()
    
    def _import_dashboards(self, dashboard_dir: Path, auth: Tuple[str, str]):
        """Import all monitoring dashboards"""
        # Check if dashboard directory exists
        if not dashboard_dir.exists():
            self.logger.error(f"Dashboard directory {dashboard_dir} not found")
            return False
            
        # Import each dashboard file
        for dashboard_file in dashboard_dir.glob("*.json"):
            try:
                with open(dashboard_file, 'r') as f:
                    dashboard = json.load(f)
                    
                response = requests.post(
                    'http://localhost:3000/api/dashboards/db',
                    json={'dashboard': dashboard['dashboard'], 'overwrite': True},
                    auth=auth
                )
                response.raise_for_status()
                self.logger.info(f"Imported dashboard: {dashboard_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to import dashboard {dashboard_file.name}: {e}")
        
        return True
    
    def _configure_grafana(self, grafana_dir: Path, env_vars: Dict[str, str]) -> bool:
        """Configure Grafana"""
        try:
            # Get configuration templates directory
            module_dir = Path(__file__).parent
            # Look for grafana config in src/monitoring/config/grafana first (legacy)
            legacy_config_dir = Path(os.path.dirname(os.path.dirname(module_dir))) / "monitoring" / "config" / "grafana"
            # If not found, look in the same directory as this module
            config_dir = legacy_config_dir if legacy_config_dir.exists() else module_dir / "config"
            
            if not config_dir.exists():
                self.logger.error(f"Grafana configuration templates not found at {config_dir}")
                return False
            
            # Prepare variables for templates
            variables = {
                'GRAFANA_ADMIN_USER': env_vars.get('GRAFANA_ADMIN_USER', 'admin'),
                'GRAFANA_ADMIN_PASSWORD': env_vars.get('GRAFANA_ADMIN_PASSWORD', 'admin'),
                'GRAFANA_SMTP_HOST': env_vars.get('GRAFANA_SMTP_HOST', ''),
                'GRAFANA_SMTP_USER': env_vars.get('GRAFANA_SMTP_USER', ''),
                'GRAFANA_SMTP_PASSWORD': env_vars.get('GRAFANA_SMTP_PASSWORD', ''),
                'GRAFANA_SMTP_FROM': env_vars.get('GRAFANA_SMTP_FROM', ''),
                'GRAFANA_ALERT_EMAIL': env_vars.get('GRAFANA_ALERT_EMAIL', ''),
                'GRAFANA_SLACK_WEBHOOK_URL': env_vars.get('GRAFANA_SLACK_WEBHOOK_URL', ''),
                'GRAFANA_SLACK_CHANNEL': env_vars.get('GRAFANA_SLACK_CHANNEL', '#alerts')
            }
            
            # Apply Grafana config template
            self._apply_template(
                config_dir / "grafana.ini",
                grafana_dir / "grafana.ini",
                variables
            )
            
            # Enable and start Grafana
            subprocess.run(["systemctl", "enable", "grafana-server"], check=True)
            subprocess.run(["systemctl", "restart", "grafana-server"], check=True)
            
            # Wait for Grafana to start
            self._wait_for_grafana()
            
            # Authentication details for Grafana API
            auth = (
                env_vars.get('GRAFANA_ADMIN_USER', 'admin'),
                env_vars.get('GRAFANA_ADMIN_PASSWORD', 'admin')
            )
            
            # Configure Prometheus datasource
            self._configure_grafana_datasource(auth)
            
            # Configure notification channels
            self._configure_grafana_notifications(config_dir, auth, env_vars)
            
            # Get dashboards directory
            dashboards_dir = config_dir / "dashboards"
            
            # Import dashboards
            self._import_dashboards(dashboards_dir, auth)
            
            return True
        except Exception as e:
            self.logger.error(f"Grafana configuration failed: {e}")
            return False
    
    def check_completed(self, grafana_dir: Path, env_vars: Dict[str, str]) -> bool:
        """Check if Grafana is properly configured"""
        try:
            # Check if Grafana is running
            status = subprocess.run(
                ["systemctl", "is-active", "grafana-server"],
                check=False,
                capture_output=True,
                text=True
            )
            
            if status.stdout.strip() != "active":
                self.logger.info("Grafana is not running")
                return False
            
            # Check if config file exists
            if not (grafana_dir / "grafana.ini").exists():
                self.logger.info("Grafana config file not found")
                return False
            
            # Check if dashboards are configured
            try:
                auth = (
                    env_vars.get('GRAFANA_ADMIN_USER', 'admin'),
                    env_vars.get('GRAFANA_ADMIN_PASSWORD', 'admin')
                )
                
                # Try to access the API to verify it's working
                response = requests.get(
                    'http://localhost:3000/api/dashboards',
                    auth=auth
                )
                response.raise_for_status()
                
                # Check if Prometheus datasource exists
                datasource_response = requests.get(
                    'http://localhost:3000/api/datasources/name/Prometheus',
                    auth=auth
                )
                
                if datasource_response.status_code != 200:
                    self.logger.info("Prometheus datasource not configured")
                    return False
                    
                return True
            except Exception as e:
                self.logger.info(f"Grafana API check failed: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return False
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute the main deployment operation"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Initialize paths
            grafana_dir = Path("/etc/grafana")
            backup_dir = Path(env_vars.get('GRAFANA_BACKUP_DIR', '/opt/fawz/keycloak/monitoring/backup/grafana'))
            
            # Ensure backup directory exists
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if already completed
            if self.check_completed(grafana_dir, env_vars):
                self.logger.info("Grafana already properly configured")
                return True
            
            # Create backup before making changes
            backup_path = self._backup_config(grafana_dir, backup_dir)
            
            # Configure Grafana
            if not self._configure_grafana(grafana_dir, env_vars):
                if backup_path:
                    self._restore_backup(backup_path, grafana_dir)
                return False
            
            self.logger.info("Grafana configuration completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Grafana configuration failed: {e}")
            if 'backup_path' in locals() and backup_path:
                self._restore_backup(backup_path, grafana_dir)
            return False
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        try:
            # Stop Grafana
            self.logger.info("Stopping Grafana service")
            subprocess.run(["systemctl", "stop", "grafana-server"], check=False)
            
            # Don't remove config files as they might be useful for debugging
            self.logger.info("Grafana cleaned up successfully")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
