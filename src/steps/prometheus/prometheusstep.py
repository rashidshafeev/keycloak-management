from ...core.base import BaseStep
import os
import subprocess
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Import step-specific modules
from .dependencies import check_prometheus_step_dependencies, install_prometheus_step_dependencies
from .environment import get_required_variables, validate_variables

class PrometheusStep(BaseStep):
    """Step for Prometheus monitoring system setup"""
    
    def __init__(self):
        super().__init__("prometheus_step", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_prometheus_step_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_prometheus_step_dependencies()
    
    def _backup_config(self, prom_dir: Path, backup_dir: Path) -> Optional[Path]:
        """Backup Prometheus configuration"""
        try:
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup Prometheus config if it exists
            if prom_dir.exists():
                shutil.copytree(
                    prom_dir,
                    backup_path,
                    dirs_exist_ok=True
                )
                self.logger.info(f"Created Prometheus backup at {backup_path}")
                
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
            
    def _restore_backup(self, backup_path: Path, prom_dir: Path) -> bool:
        """Restore Prometheus configuration from backup"""
        try:
            if backup_path.exists():
                # Remove current config
                if prom_dir.exists():
                    shutil.rmtree(prom_dir)
                
                # Restore from backup
                shutil.copytree(
                    backup_path,
                    prom_dir,
                    dirs_exist_ok=True
                )
                
                # Restart Prometheus
                subprocess.run(["systemctl", "restart", "prometheus"], check=False)
                
                self.logger.info(f"Restored Prometheus configuration from {backup_path}")
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
    
    def _configure_prometheus(self, prom_dir: Path, env_vars: Dict[str, str]) -> bool:
        """Configure Prometheus"""
        try:
            # Get configuration templates directory
            module_dir = Path(__file__).parent
            # Look for prometheus config in src/monitoring/config/prometheus first (legacy)
            legacy_config_dir = Path(os.path.dirname(os.path.dirname(module_dir))) / "monitoring" / "config" / "prometheus"
            # If not found, look in the same directory as this module
            config_dir = legacy_config_dir if legacy_config_dir.exists() else module_dir / "config"
            
            if not config_dir.exists():
                self.logger.error(f"Prometheus configuration templates not found at {config_dir}")
                return False
            
            # Prepare variables
            variables = {
                'PROMETHEUS_SCRAPE_INTERVAL': env_vars.get('PROMETHEUS_SCRAPE_INTERVAL', '15s'),
                'PROMETHEUS_EVAL_INTERVAL': env_vars.get('PROMETHEUS_EVAL_INTERVAL', '15s'),
                'PROMETHEUS_RETENTION_TIME': env_vars.get('PROMETHEUS_RETENTION_TIME', '15d')
            }
            
            # Apply main config template
            self._apply_template(
                config_dir / "prometheus.yml",
                prom_dir / "prometheus.yml",
                variables
            )
            
            # Copy scrape configs
            shutil.copy2(
                config_dir / "scrape_configs.yml",
                prom_dir / "scrape_configs.yml"
            )
            
            # Copy alert rules
            alerts_dir = prom_dir / "alerts"
            alerts_dir.mkdir(parents=True, exist_ok=True)
            
            for alert_file in (config_dir / "alerts").glob("*.yml"):
                shutil.copy2(alert_file, alerts_dir / alert_file.name)
                
            # Configure Docker metrics
            docker_metrics_port = env_vars.get('DOCKER_METRICS_PORT', '9323')
            docker_config = {
                'metrics-addr': f'localhost:{docker_metrics_port}',
                'experimental': True
            }
            
            docker_daemon_file = Path("/etc/docker/daemon.json")
            docker_daemon_file.parent.mkdir(parents=True, exist_ok=True)
            
            # If the file exists, read it and update metrics config
            if docker_daemon_file.exists():
                with open(docker_daemon_file, 'r') as f:
                    try:
                        existing_config = json.load(f)
                        existing_config.update(docker_config)
                        docker_config = existing_config
                    except json.JSONDecodeError:
                        # If the file exists but is invalid JSON, we'll overwrite it
                        self.logger.warning(f"Invalid JSON in {docker_daemon_file}, overwriting")
            
            # Write Docker configuration
            with open(docker_daemon_file, 'w') as f:
                json.dump(docker_config, f, indent=2)
            
            # Restart Docker to apply metrics configuration
            subprocess.run(["systemctl", "restart", "docker"], check=False)
            
            # Enable and start Prometheus
            subprocess.run(["systemctl", "enable", "prometheus"], check=True)
            subprocess.run(["systemctl", "restart", "prometheus"], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Prometheus configuration failed: {e}")
            return False
    
    def check_completed(self, prom_dir: Path) -> bool:
        """Check if Prometheus is properly configured"""
        try:
            # Check if Prometheus is running
            status = subprocess.run(
                ["systemctl", "is-active", "prometheus"],
                check=False,
                capture_output=True,
                text=True
            )
            
            if status.stdout.strip() != "active":
                self.logger.info("Prometheus is not running")
                return False
            
            # Check if config file exists
            if not (prom_dir / "prometheus.yml").exists():
                self.logger.info("Prometheus config file not found")
                return False
                
            # Check if alerts directory exists and has files
            alerts_dir = prom_dir / "alerts"
            if not alerts_dir.exists() or not any(alerts_dir.iterdir()):
                self.logger.info("Prometheus alerts directory not found or empty")
                return False
                
            return True
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
            prom_dir = Path("/etc/prometheus")
            backup_dir = Path(env_vars.get('PROMETHEUS_BACKUP_DIR', '/opt/fawz/keycloak/monitoring/backup/prometheus'))
            
            # Ensure backup directory exists
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if already completed
            if self.check_completed(prom_dir):
                self.logger.info("Prometheus already properly configured")
                return True
            
            # Create backup before making changes
            backup_path = self._backup_config(prom_dir, backup_dir)
            
            # Configure Prometheus
            if not self._configure_prometheus(prom_dir, env_vars):
                if backup_path:
                    self._restore_backup(backup_path, prom_dir)
                return False
            
            self.logger.info("Prometheus configuration completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Prometheus configuration failed: {e}")
            if 'backup_path' in locals() and backup_path:
                self._restore_backup(backup_path, prom_dir)
            return False
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        try:
            # Stop Prometheus
            self.logger.info("Stopping Prometheus service")
            subprocess.run(["systemctl", "stop", "prometheus"], check=False)
            
            # Don't remove config files as they might be useful for debugging
            self.logger.info("Prometheus cleaned up successfully")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
