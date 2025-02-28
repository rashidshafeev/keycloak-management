from ...core.base import BaseStep
import subprocess
import logging
import os
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import shutil

# Import step-specific modules
from .dependencies import check_firewallstep_dependencies, install_firewallstep_dependencies
from .environment import get_required_variables, validate_variables

class FirewallStep(BaseStep):
    """Step for configuring system firewall rules"""
    
    def __init__(self):
        super().__init__("firewall_configuration", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_firewallstep_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_firewallstep_dependencies()
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute firewall configuration"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Set up directory structure
            rules_dir = Path(env_vars.get('FIREWALL_RULES_DIR', '/etc/keycloak/firewall/rules'))
            backup_dir = Path(env_vars.get('FIREWALL_BACKUP_DIR', '/etc/keycloak/firewall/backup'))
            max_backups = int(env_vars.get('FIREWALL_MAX_BACKUPS', '5'))
            
            # Create directories if they don't exist
            rules_dir.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Define required ports for Keycloak
            required_ports = {
                'https': env_vars.get('KEYCLOAK_PORT', '8443'),
                'http': env_vars.get('KEYCLOAK_HTTP_PORT', '8080'),
                'management': env_vars.get('KEYCLOAK_MANAGEMENT_PORT', '9990'),
                'ajp': env_vars.get('KEYCLOAK_AJP_PORT', '8009')
            }
            
            # Migrate from UFW if present
            self._migrate_from_ufw()
            
            # Load existing rules
            existing_rules = self._load_rules(rules_dir)
            
            # Add default rules for Keycloak
            for protocol, port in required_ports.items():
                rule_name = f"{protocol}_in"
                if rule_name not in existing_rules:
                    existing_rules[rule_name] = {
                        "port": port,
                        "protocol": "tcp",
                        "source": "0.0.0.0/0"
                    }
            
            # Save rules to file
            self._save_rules(rules_dir, existing_rules)
            
            # Create backup before applying changes
            self._backup_rules(rules_dir, backup_dir, max_backups)
            
            # Apply rules to iptables
            self._apply_rules(existing_rules)
            
            # Set up fail2ban if available
            self._setup_fail2ban(env_vars)
            
            self.logger.info("Firewall configuration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure firewall: {str(e)}")
            return False
    
    def _migrate_from_ufw(self) -> None:
        """Migrate existing UFW rules to iptables"""
        try:
            # Check if UFW is active
            result = self._run_command(
                ["ufw", "status"],
                check=False
            )
            
            if result.returncode == 0 and "Status: active" in result.stdout:
                self.logger.info("Found active UFW configuration, migrating...")
                
                # Extract UFW rules
                rules = self._run_command(
                    ["ufw", "show", "added"],
                    check=False
                )
                
                if rules.returncode == 0:
                    # Parse and convert UFW rules to iptables
                    for line in rules.stdout.splitlines():
                        if "allow" in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                port = parts[3]
                                source = parts[1] if parts[1] != "Anywhere" else "0.0.0.0/0"
                                
                                try:
                                    self._run_command([
                                        "iptables", "-A", "INPUT",
                                        "-p", "tcp",
                                        "-s", source,
                                        "--dport", port,
                                        "-j", "ACCEPT"
                                    ])
                                except Exception as e:
                                    self.logger.warning(f"Failed to migrate rule: {line}, error: {str(e)}")
                    
                    # Disable UFW after migration
                    self._run_command(["ufw", "--force", "disable"], check=False)
                    self.logger.info("Successfully migrated from UFW to iptables")
                
        except Exception as e:
            self.logger.warning(f"UFW migration failed (this is ok if UFW was not used): {str(e)}")
    
    def _load_rules(self, rules_dir: Path) -> Dict[str, Dict]:
        """Load firewall rules from file"""
        rules_file = rules_dir / "rules.json"
        try:
            if rules_file.exists():
                with open(rules_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load existing rules: {str(e)}")
        
        return {}
    
    def _save_rules(self, rules_dir: Path, rules: Dict[str, Dict]) -> None:
        """Save firewall rules to file"""
        rules_file = rules_dir / "rules.json"
        with open(rules_file, "w") as f:
            json.dump(rules, f, indent=2)
        self.logger.debug(f"Rules saved to {rules_file}")
    
    def _backup_rules(self, rules_dir: Path, backup_dir: Path, max_backups: int) -> None:
        """Backup existing rules file"""
        rules_file = rules_dir / "rules.json"
        if not rules_file.exists():
            return
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = backup_dir / f"rules_{timestamp}.json"
        
        shutil.copy(rules_file, backup_path)
        self.logger.info(f"Created firewall rules backup: {backup_path}")
        
        # Cleanup old backups if we have too many
        backups = sorted(backup_dir.glob("rules_*.json"), key=lambda p: p.stat().st_mtime)
        if len(backups) > max_backups:
            for old_backup in backups[:(len(backups) - max_backups)]:
                try:
                    old_backup.unlink()
                    self.logger.debug(f"Removed old backup: {old_backup}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove old backup {old_backup}: {str(e)}")
    
    def _apply_rules(self, rules: Dict[str, Dict]) -> None:
        """Apply rules to iptables"""
        # Flush existing rules
        self._run_command(["iptables", "-F"])
        self._run_command(["iptables", "-X"])
        
        # Set default policies
        self._run_command(["iptables", "-P", "INPUT", "DROP"])
        self._run_command(["iptables", "-P", "FORWARD", "DROP"])
        self._run_command(["iptables", "-P", "OUTPUT", "ACCEPT"])
        
        # Allow established connections and loopback
        self._run_command([
            "iptables", "-A", "INPUT", 
            "-m", "conntrack", 
            "--ctstate", "ESTABLISHED,RELATED", 
            "-j", "ACCEPT"
        ])
        self._run_command(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
        
        # Apply rules
        for rule_name, rule_config in rules.items():
            port = rule_config.get('port')
            protocol = rule_config.get('protocol', 'tcp')
            source = rule_config.get('source', '0.0.0.0/0')
            
            if port:
                self._run_command([
                    "iptables", "-A", "INPUT",
                    "-p", protocol,
                    "-s", source,
                    "--dport", str(port),
                    "-j", "ACCEPT"
                ])
                self.logger.info(f"Applied rule {rule_name}: Allow {protocol} port {port} from {source}")
    
    def _setup_fail2ban(self, env_vars: Dict[str, str]) -> None:
        """Set up fail2ban if available"""
        try:
            # Check if fail2ban is installed
            result = self._run_command(["systemctl", "status", "fail2ban"], check=False)
            if result.returncode != 0:
                self.logger.warning("fail2ban service not found, skipping configuration")
                return
                
            # Enable and start fail2ban
            self._run_command(["systemctl", "enable", "fail2ban"])
            self._run_command(["systemctl", "start", "fail2ban"])
            self.logger.info("fail2ban service enabled and started")
            
            # Configure keycloak jail if not present
            fail2ban_dir = Path("/etc/fail2ban")
            jail_local = fail2ban_dir / "jail.local"
            
            if not fail2ban_dir.exists():
                self.logger.warning("fail2ban configuration directory not found, skipping keycloak jail setup")
                return
                
            # Simple keycloak jail configuration
            keycloak_jail = """
[keycloak]
enabled = true
filter = keycloak
logpath = /var/log/keycloak/server.log
maxretry = 5
bantime = 3600
action = iptables-multiport[name=keycloak, port="8080,8443,9990"]
"""
            
            if not jail_local.exists() or "keycloak" not in jail_local.read_text():
                with open(jail_local, "a") as f:
                    f.write(keycloak_jail)
                
                # Create keycloak filter if it doesn't exist
                filter_dir = fail2ban_dir / "filter.d"
                filter_dir.mkdir(exist_ok=True)
                
                filter_file = filter_dir / "keycloak.conf"
                if not filter_file.exists():
                    with open(filter_file, "w") as f:
                        f.write("""[Definition]
failregex = ^.*Login failed.* ip_address=<HOST>.*$
            ^.*Invalid user credentials.* ip_address=<HOST>.*$
ignoreregex =
""")
                
                # Restart fail2ban to apply changes
                self._run_command(["systemctl", "restart", "fail2ban"])
                self.logger.info("Configured fail2ban for Keycloak")
                
        except Exception as e:
            self.logger.warning(f"Failed to set up fail2ban: {str(e)}")
    
    def _cleanup(self) -> None:
        """Clean up firewall rules and configurations"""
        try:
            # Reset iptables to accept all traffic
            self._run_command(["iptables", "-F"], check=False)
            self._run_command(["iptables", "-X"], check=False)
            self._run_command(["iptables", "-P", "INPUT", "ACCEPT"], check=False)
            self._run_command(["iptables", "-P", "FORWARD", "ACCEPT"], check=False)
            self._run_command(["iptables", "-P", "OUTPUT", "ACCEPT"], check=False)
            
            self.logger.info("Firewall rules have been reset to accept all traffic")
            
            # Optionally, stop fail2ban
            self._run_command(["systemctl", "stop", "fail2ban"], check=False)
            self.logger.info("fail2ban service has been stopped")
            
        except Exception as e:
            self.logger.warning(f"Firewall cleanup failed: {str(e)}")
