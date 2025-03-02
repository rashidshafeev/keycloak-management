from ...core.base import BaseStep
import subprocess
from pathlib import Path
import logging
import json
import yaml
from typing import Dict, List, Optional, Tuple
import os
import shutil
from datetime import datetime
import requests
import time

# Import step-specific modules
from .dependencies import check_wazuh_step_dependencies, install_wazuh_step_dependencies
from .environment import get_required_variables, validate_variables

class WazuhStep(BaseStep):
    """Step for security monitoring with Wazuh"""
    
    def __init__(self):
        super().__init__("wazuh_management", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_wazuh_step_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_wazuh_step_dependencies()
    
    def _backup_config(self, backup_dir: Path, wazuh_dir: Path) -> Optional[Path]:
        """Backup Wazuh configuration"""
        try:
            # List and sort backups by date
            backup_dir.mkdir(parents=True, exist_ok=True)
            backups = sorted(backup_dir.glob('*'))
            
            # Remove old backups if we exceed max_backups
            max_backups = 5  # Default
            while len(backups) >= max_backups:
                oldest = backups.pop(0)
                shutil.rmtree(oldest)
                self.logger.info(f"Removed old backup: {oldest}")
                
            # Create new backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            if wazuh_dir.exists():
                # Backup main configuration
                ossec_config = wazuh_dir / "etc/ossec.conf"
                if ossec_config.exists():
                    shutil.copy2(ossec_config, backup_path / "ossec.conf")
                
                # Backup custom rules
                rules_dir = wazuh_dir / "etc/rules"
                if rules_dir.exists():
                    shutil.copytree(
                        rules_dir,
                        backup_path / "rules",
                        dirs_exist_ok=True
                    )
                    
                # Backup local internal options
                local_options = wazuh_dir / "etc/local_internal_options.conf"
                if local_options.exists():
                    shutil.copy2(local_options, backup_path / "local_internal_options.conf")
                    
            self.logger.info(f"Created Wazuh backup at {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
    
    def _restore_backup(self, backup_path: Path, wazuh_dir: Path) -> bool:
        """Restore Wazuh configuration from backup"""
        try:
            # Restore main configuration
            if (backup_path / "ossec.conf").exists():
                shutil.copy2(
                    backup_path / "ossec.conf",
                    wazuh_dir / "etc/ossec.conf"
                )
                
            # Restore custom rules
            rules_backup = backup_path / "rules"
            if rules_backup.exists():
                rules_dir = wazuh_dir / "etc/rules"
                rules_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    rules_backup,
                    rules_dir,
                    dirs_exist_ok=True
                )
                
            # Restore local internal options
            if (backup_path / "local_internal_options.conf").exists():
                shutil.copy2(
                    backup_path / "local_internal_options.conf",
                    wazuh_dir / "etc/local_internal_options.conf"
                )
                
            # Restart Wazuh
            subprocess.run(["systemctl", "restart", "wazuh-manager"], check=True)
            self.logger.info(f"Restored Wazuh configuration from {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def _configure_wazuh_manager(self, wazuh_dir: Path, manager_config: Dict) -> bool:
        """Configure Wazuh manager"""
        try:
            # Basic ossec.conf template
            ossec_config = f"""
<ossec_config>
  <global>
    <email_notification>yes</email_notification>
    <email_to>{manager_config['notification_email']}</email_to>
    <smtp_server>localhost</smtp_server>
    <email_from>wazuh@localhost</email_from>
  </global>
  <alerts>
    <log_alert_level>{manager_config['alert_level']}</log_alert_level>
  </alerts>
  <syscheck>
    <directories check_all="yes">/var/log/keycloak</directories>
    <directories check_all="yes">{wazuh_dir}/logs/alerts</directories>
    <alert_new_files>yes</alert_new_files>
  </syscheck>
  <rootcheck>
    <system_audit>/var/ossec/etc/shared/system_audit_rcl.txt</system_audit>
    <system_audit>/var/ossec/etc/shared/system_audit_ssh.txt</system_audit>
    <system_audit>/var/ossec/etc/shared/cis_debian_linux_rcl.txt</system_audit>
  </rootcheck>
  <remote>
    <connection>{manager_config['protocol']}</connection>
    <port>{manager_config['port']}</port>
  </remote>
  <command>
    <n>restart-keycloak</n>
    <executable>restart-keycloak.sh</executable>
    <expect />
  </command>
  <active-response>
    <command>restart-keycloak</command>
    <location>local</location>
    <rules_id>100100</rules_id>
  </active-response>
</ossec_config>
            """
            
            # Write configuration
            os.makedirs(wazuh_dir / "etc", exist_ok=True)
            with open(wazuh_dir / "etc/ossec.conf", 'w') as f:
                f.write(ossec_config)
                
            # Create custom rules for Keycloak
            keycloak_rules = """
<group name="keycloak,">
  <rule id="100100" level="10">
    <if_sid>530</if_sid>
    <match>Multiple authentication failures</match>
    <description>Multiple failed login attempts on Keycloak.</description>
    <group>authentication_failures,</group>
  </rule>
  <rule id="100101" level="10">
    <if_sid>530</if_sid>
    <match>Possible brute force attack</match>
    <description>Possible brute force attack on Keycloak detected.</description>
    <group>brute_force,</group>
  </rule>
  <rule id="100102" level="12">
    <if_sid>530</if_sid>
    <match>Administrative access attempt</match>
    <description>Unauthorized administrative access attempt on Keycloak.</description>
    <group>administrative_access,</group>
  </rule>
  <rule id="100103" level="7">
    <if_sid>530</if_sid>
    <match>Configuration changed</match>
    <description>Keycloak configuration has been modified.</description>
    <group>configuration_changes,</group>
  </rule>
</group>
            """
            
            # Write custom rules
            rules_dir = wazuh_dir / "etc/rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            with open(rules_dir / "keycloak_rules.xml", 'w') as f:
                f.write(keycloak_rules)
                
            # Create restart script
            restart_script = """#!/bin/bash
systemctl restart keycloak
            """
            
            script_path = wazuh_dir / "active-response/bin/restart-keycloak.sh"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, 'w') as f:
                f.write(restart_script)
            os.chmod(script_path, 0o750)
            
            # Restart Wazuh
            subprocess.run(["systemctl", "restart", "wazuh-manager"], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Wazuh configuration failed: {e}")
            return False
    
    def _configure_file_monitoring(self, wazuh_dir: Path) -> bool:
        """Configure file integrity monitoring for Keycloak"""
        try:
            fim_config = """
<syscheck>
  <!-- Keycloak configuration files -->
  <directories check_all="yes" realtime="yes">/opt/keycloak/conf</directories>
  
  <!-- Keycloak data directory -->
  <directories check_all="yes" realtime="yes">/opt/keycloak/data</directories>
  
  <!-- Keycloak log files -->
  <directories check_all="yes" realtime="yes">/opt/keycloak/log</directories>
  
  <!-- Frequency for file checking -->
  <frequency>3600</frequency>
  
  <!-- Don't process these files -->
  <ignore>/opt/keycloak/log/*.log</ignore>
  <ignore type="sregex">.log$|.tmp$|.swp$</ignore>
  
  <!-- Alert when new files are created -->
  <alert_new_files>yes</alert_new_files>
</syscheck>
            """
            
            # Add FIM configuration to ossec.conf
            with open(wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<syscheck>" not in content:
                    f.write(fim_config)
            return True
        except Exception as e:
            self.logger.error(f"File monitoring configuration failed: {e}")
            return False
    
    def _configure_policy_monitoring(self, wazuh_dir: Path) -> bool:
        """Configure security policy monitoring"""
        try:
            policy_config = """
<rootcheck>
  <!-- System audit files -->
  <system_audit>/var/ossec/etc/shared/system_audit_rcl.txt</system_audit>
  <system_audit>/var/ossec/etc/shared/system_audit_ssh.txt</system_audit>
  <system_audit>/var/ossec/etc/shared/cis_debian_linux_rcl.txt</system_audit>
  
  <!-- Policy monitoring -->
  <check_unixaudit>yes</check_unixaudit>
  <check_sys>yes</check_sys>
  <check_pids>yes</check_pids>
  <check_ports>yes</check_ports>
  <check_if>yes</check_if>
  
  <!-- Frequency -->
  <frequency>86400</frequency>
</rootcheck>
            """
            
            # Add policy monitoring configuration to ossec.conf
            with open(wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<rootcheck>" not in content:
                    f.write(policy_config)
            return True
        except Exception as e:
            self.logger.error(f"Policy monitoring configuration failed: {e}")
            return False
    
    def _configure_alerts(self, wazuh_dir: Path, manager_config: Dict) -> bool:
        """Configure alerting system"""
        try:
            alerts_config = f"""
<global>
  <email_notification>yes</email_notification>
  <email_to>{manager_config['notification_email']}</email_to>
  <smtp_server>localhost</smtp_server>
  <email_from>wazuh@localhost</email_from>
  <email_maxperhour>12</email_maxperhour>
</global>
<alerts>
  <log_alert_level>{manager_config['alert_level']}</log_alert_level>
  <email_alert_level>7</email_alert_level>
</alerts>
            """
            
            # Add alerts configuration to ossec.conf
            with open(wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<global>" not in content:
                    f.write(alerts_config)
            return True
        except Exception as e:
            self.logger.error(f"Alerts configuration failed: {e}")
            return False
    
    def check_completed(self, wazuh_dir: Path) -> bool:
        """Check if Wazuh is properly installed and configured"""
        try:
            # Check if Wazuh manager is running
            result = subprocess.run(
                ["systemctl", "is-active", "wazuh-manager"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
                
            # Check if configuration file exists
            if not (wazuh_dir / "etc/ossec.conf").exists():
                return False
                
            # Check if custom rules exist
            if not (wazuh_dir / "etc/rules/keycloak_rules.xml").exists():
                return False
                
            # Check if restart script exists
            if not (wazuh_dir / "active-response/bin/restart-keycloak.sh").exists():
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
            # Initialize paths and configuration
            wazuh_dir = Path("/var/ossec")
            backup_dir = Path(env_vars.get('WAZUH_BACKUP_DIR', '/opt/fawz/keycloak/wazuh/backup'))
            config_dir = Path(env_vars.get('WAZUH_CONFIG_DIR', '/opt/fawz/keycloak/wazuh/config'))
            max_backups = int(env_vars.get('WAZUH_MAX_BACKUPS', '5'))
            
            # Prepare directories
            backup_dir.mkdir(parents=True, exist_ok=True)
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if already completed
            if self.check_completed(wazuh_dir):
                self.logger.info("Wazuh already properly configured")
                return True
                
            # Create backup before making changes
            backup_path = self._backup_config(backup_dir, wazuh_dir)
            
            # Initialize manager configuration
            manager_config = {
                'port': int(env_vars.get('WAZUH_MANAGER_PORT', '1514')),
                'protocol': env_vars.get('WAZUH_PROTOCOL', 'tcp'),
                'notification_email': env_vars.get('WAZUH_NOTIFICATION_EMAIL'),
                'alert_level': int(env_vars.get('WAZUH_ALERT_LEVEL', '7'))
            }
            
            # Configure Wazuh manager
            self.logger.info("Configuring Wazuh manager...")
            if not self._configure_wazuh_manager(wazuh_dir, manager_config):
                if backup_path:
                    self._restore_backup(backup_path, wazuh_dir)
                return False
                
            # Configure file monitoring
            self.logger.info("Configuring file integrity monitoring...")
            if not self._configure_file_monitoring(wazuh_dir):
                if backup_path:
                    self._restore_backup(backup_path, wazuh_dir)
                return False
                
            # Configure policy monitoring
            self.logger.info("Configuring security policy monitoring...")
            if not self._configure_policy_monitoring(wazuh_dir):
                if backup_path:
                    self._restore_backup(backup_path, wazuh_dir)
                return False
                
            # Configure alerts
            self.logger.info("Configuring alert system...")
            if not self._configure_alerts(wazuh_dir, manager_config):
                if backup_path:
                    self._restore_backup(backup_path, wazuh_dir)
                return False
                
            # Wait for Wazuh to start
            self.logger.info("Waiting for Wazuh manager to start...")
            max_retries = 12
            retry_interval = 5
            for i in range(max_retries):
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", "wazuh-manager"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        break
                except Exception:
                    pass
                    
                if i < max_retries - 1:
                    time.sleep(retry_interval)
            else:
                self.logger.error("Wazuh failed to start")
                if backup_path:
                    self._restore_backup(backup_path, wazuh_dir)
                return False
                
            self.logger.info("Wazuh configuration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Wazuh configuration failed: {e}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        try:
            # Stop Wazuh services
            self.logger.info("Stopping Wazuh services...")
            subprocess.run(["systemctl", "stop", "wazuh-manager"], check=False)
            subprocess.run(["systemctl", "stop", "wazuh-indexer"], check=False)
            subprocess.run(["systemctl", "stop", "wazuh-dashboard"], check=False)
            
            # Clean up is limited to stopping services - we don't want to remove 
            # installed packages or configuration files as that might be destructive
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")