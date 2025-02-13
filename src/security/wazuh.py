from ..deployment.base import DeploymentStep
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

class WazuhManager(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("wazuh_management", can_cleanup=False)
        self.config = config
        self.wazuh_dir = Path("/var/ossec")
        self.backup_dir = Path("/opt/fawz/keycloak/wazuh/backup")
        self.config_dir = Path("/opt/fawz/keycloak/wazuh/config")
        self.max_backups = self.config.get("wazuh", {}).get("max_backups", 5)
        
        # Wazuh manager configuration
        self.manager_config = {
            'port': self.config.get("wazuh", {}).get("manager_port", 1514),
            'protocol': self.config.get("wazuh", {}).get("protocol", "tcp"),
            'notification_email': self.config.get("wazuh", {}).get("notification_email"),
            'alert_level': self.config.get("wazuh", {}).get("alert_level", 3)
        }

    def _backup_config(self) -> Optional[Path]:
        """Backup Wazuh configuration"""
        try:
            # List and sort backups by date
            backups = sorted(self.backup_dir.glob('*'))
            
            # Remove old backups if we exceed max_backups
            while len(backups) >= self.max_backups:
                oldest = backups.pop(0)
                shutil.rmtree(oldest)
                self.logger.info(f"Removed old backup: {oldest}")

            # Create new backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)

            if self.wazuh_dir.exists():
                # Backup main configuration
                shutil.copy2(
                    self.wazuh_dir / "etc/ossec.conf",
                    backup_path / "ossec.conf"
                )
                
                # Backup custom rules
                rules_dir = self.wazuh_dir / "etc/rules"
                if rules_dir.exists():
                    shutil.copytree(
                        rules_dir,
                        backup_path / "rules",
                        dirs_exist_ok=True
                    )

                # Backup local internal options
                shutil.copy2(
                    self.wazuh_dir / "etc/local_internal_options.conf",
                    backup_path / "local_internal_options.conf"
                )

            self.logger.info(f"Created Wazuh backup at {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None

    def _restore_backup(self, backup_path: Optional[Path] = None) -> bool:
        """Restore Wazuh configuration from backup"""
        try:
            if not backup_path:
                backups = sorted(self.backup_dir.glob('*'), reverse=True)
                if not backups:
                    return False
                backup_path = backups[0]

            # Restore main configuration
            shutil.copy2(
                backup_path / "ossec.conf",
                self.wazuh_dir / "etc/ossec.conf"
            )

            # Restore custom rules
            rules_backup = backup_path / "rules"
            if rules_backup.exists():
                shutil.copytree(
                    rules_backup,
                    self.wazuh_dir / "etc/rules",
                    dirs_exist_ok=True
                )

            # Restore local internal options
            shutil.copy2(
                backup_path / "local_internal_options.conf",
                self.wazuh_dir / "etc/local_internal_options.conf"
            )

            # Restart Wazuh
            subprocess.run(["systemctl", "restart", "wazuh-manager"], check=True)

            self.logger.info(f"Restored Wazuh configuration from {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False

    def _install_wazuh_manager(self) -> bool:
        """Install Wazuh manager"""
        try:
            # Add Wazuh repository
            subprocess.run([
                "curl", "-s", "https://packages.wazuh.com/key/GPG-KEY-WAZUH",
                "-o", "/usr/share/keyrings/wazuh.gpg"
            ], check=True)

            subprocess.run([
                "echo", "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main",
                ">", "/etc/apt/sources.list.d/wazuh.list"
            ], check=True)

            # Update and install
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run([
                "apt-get", "install", "-y", 
                "wazuh-manager",
                "wazuh-indexer",
                "wazuh-dashboard"
            ], check=True)

            return True
        except Exception as e:
            self.logger.error(f"Wazuh installation failed: {e}")
            return False

    def _configure_wazuh_manager(self) -> bool:
        """Configure Wazuh manager"""
        try:
            # Basic ossec.conf template
            ossec_config = f"""
<ossec_config>
  <global>
    <email_notification>yes</email_notification>
    <email_to>{self.manager_config['notification_email']}</email_to>
    <smtp_server>localhost</smtp_server>
    <email_from>wazuh@localhost</email_from>
  </global>

  <alerts>
    <log_alert_level>{self.manager_config['alert_level']}</log_alert_level>
  </alerts>

  <syscheck>
    <directories check_all="yes">/var/log/keycloak</directories>
    <directories check_all="yes">{self.wazuh_dir}/logs/alerts</directories>
    <alert_new_files>yes</alert_new_files>
  </syscheck>

  <rootcheck>
    <system_audit>/var/ossec/etc/shared/system_audit_rcl.txt</system_audit>
    <system_audit>/var/ossec/etc/shared/system_audit_ssh.txt</system_audit>
    <system_audit>/var/ossec/etc/shared/cis_debian_linux_rcl.txt</system_audit>
  </rootcheck>

  <remote>
    <connection>{self.manager_config['protocol']}</connection>
    <port>{self.manager_config['port']}</port>
  </remote>

  <command>
    <name>restart-keycloak</name>
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
            with open(self.wazuh_dir / "etc/ossec.conf", 'w') as f:
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
            rules_dir = self.wazuh_dir / "etc/rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            with open(rules_dir / "keycloak_rules.xml", 'w') as f:
                f.write(keycloak_rules)

            # Create restart script
            restart_script = """#!/bin/bash
systemctl restart keycloak
            """
            
            script_path = self.wazuh_dir / "active-response/bin/restart-keycloak.sh"
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

    def _configure_file_monitoring(self) -> bool:
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
            with open(self.wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<syscheck>" not in content:
                    f.write(fim_config)

            return True
        except Exception as e:
            self.logger.error(f"File monitoring configuration failed: {e}")
            return False

    def _configure_policy_monitoring(self) -> bool:
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
            with open(self.wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<rootcheck>" not in content:
                    f.write(policy_config)

            return True
        except Exception as e:
            self.logger.error(f"Policy monitoring configuration failed: {e}")
            return False

    def _configure_alerts(self) -> bool:
        """Configure alerting system"""
        try:
            alerts_config = f"""
<global>
  <email_notification>yes</email_notification>
  <email_to>{self.manager_config['notification_email']}</email_to>
  <smtp_server>localhost</smtp_server>
  <email_from>wazuh@localhost</email_from>
  <email_maxperhour>12</email_maxperhour>
</global>

<alerts>
  <log_alert_level>{self.manager_config['alert_level']}</log_alert_level>
  <email_alert_level>7</email_alert_level>
</alerts>
            """

            # Add alerts configuration to ossec.conf
            with open(self.wazuh_dir / "etc/ossec.conf", 'r+') as f:
                content = f.read()
                if "<global>" not in content:
                    f.write(alerts_config)

            return True
        except Exception as e:
            self.logger.error(f"Alerts configuration failed: {e}")
            return False

    def check_completed(self) -> bool:
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
            if not (self.wazuh_dir / "etc/ossec.conf").exists():
                return False

            # Check if custom rules exist
            if not (self.wazuh_dir / "etc/rules/keycloak_rules.xml").exists():
                return False

            # Check if restart script exists
            if not (self.wazuh_dir / "active-response/bin/restart-keycloak.sh").exists():
                return False

            return True
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return False

    def execute(self) -> bool:
        """Install and configure Wazuh"""
        try:
            if self.check_completed():
                self.logger.info("Wazuh already properly configured")
                return True

            # Create backup before making changes
            backup_path = self._backup_config()

            # Install Wazuh manager
            if not self._install_wazuh_manager():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Configure Wazuh manager
            if not self._configure_wazuh_manager():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Configure file monitoring
            if not self._configure_file_monitoring():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Configure policy monitoring
            if not self._configure_policy_monitoring():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Configure alerts
            if not self._configure_alerts():
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            # Wait for Wazuh to start
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
                except:
                    pass
                if i < max_retries - 1:
                    time.sleep(retry_interval)
            else:
                self.logger.error("Wazuh failed to start")
                if backup_path:
                    self._restore_backup(backup_path)
                return False

            self.logger.info("Wazuh configuration completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Wazuh configuration failed: {e}")
            if backup_path:
                self._restore_backup(backup_path)
            return False
