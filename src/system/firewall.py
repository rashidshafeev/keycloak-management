from ..deployment.base import DeploymentStep
import subprocess
from pathlib import Path
import logging
import json
from typing import List, Dict, Optional, Tuple
import ipaddress
import yaml
from datetime import datetime
import shutil
import os

class FirewallManager(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("firewall_management", can_cleanup=False)
        self.config = config
        self.rules_dir = Path("/etc/fawz/keycloak/firewall/rules")
        self.backup_dir = Path("/etc/fawz/keycloak/firewall/backup")
        self.fail2ban_dir = Path("/etc/fail2ban")
        self.max_backups = self.config.get("firewall", {}).get("max_backups", 5)
        
        # Default ports for Keycloak
        self.required_ports = {
            'http': 8080,
            'https': 8443,
            'management': 9990,
            'ajp': 8009
        }

        # Migrate from old UFW config if present
        self._migrate_from_ufw()

    def check_completed(self) -> bool:
        try:
            result = subprocess.run(
                ["iptables", "-n", "-L"],
                capture_output=True,
                text=True
            )
            return any(str(port) in result.stdout for port in self.required_ports.values())
        except Exception:
            return False

    def execute(self) -> bool:
        try:
            # Create rules directory if it doesn't exist
            if not self.rules_dir.exists():
                self.rules_dir.mkdir(parents=True)

            # Create backup directory if it doesn't exist
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True)

            # Load existing rules
            existing_rules = self._load_rules()

            # Add default rules for Keycloak
            for protocol, port in self.required_ports.items():
                if f"{protocol}_in" not in existing_rules:
                    existing_rules.append(f"{protocol}_in")

            # Add custom rules from configuration
            for rule in self.config.get("firewall", {}).get("rules", []):
                if rule not in existing_rules:
                    existing_rules.append(rule)

            # Save rules to file
            self._save_rules(existing_rules)

            # Apply rules to iptables
            self._apply_rules(existing_rules)

            # Enable and start fail2ban
            subprocess.run(["systemctl", "enable", "fail2ban"], check=True)
            subprocess.run(["systemctl", "start", "fail2ban"], check=True)

            return True
        except Exception as e:
            self.logger.error(f"Failed to setup firewall: {e}")
            return False

    def _migrate_from_ufw(self):
        """Migrate existing UFW rules to iptables"""
        try:
            # Check if UFW is active
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True
            )
            
            if "Status: active" in result.stdout:
                self.logger.info("Found active UFW configuration, migrating...")
                
                # Extract UFW rules
                rules = subprocess.run(
                    ["ufw", "show", "added"],
                    capture_output=True,
                    text=True
                ).stdout

                # Parse and convert UFW rules to iptables
                for line in rules.splitlines():
                    if "allow" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            port = parts[3]
                            source = parts[1] if parts[1] != "Anywhere" else "0.0.0.0/0"
                            
                            subprocess.run([
                                "iptables", "-A", "INPUT",
                                "-p", "tcp",
                                "-s", source,
                                "--dport", port,
                                "-j", "ACCEPT"
                            ], check=True)

                # Disable UFW after migration
                subprocess.run(["ufw", "--force", "disable"], check=True)
                self.logger.info("Successfully migrated from UFW to iptables")
                
        except Exception as e:
            self.logger.warning(f"UFW migration failed (this is ok if UFW was not used): {e}")

    def _load_rules(self) -> List[str]:
        try:
            with open(self.rules_dir / "rules.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_rules(self, rules: List[str]) -> None:
        with open(self.rules_dir / "rules.json", "w") as f:
            json.dump(rules, f)

    def _apply_rules(self, rules: List[str]) -> None:
        # Flush existing rules
        subprocess.run(["iptables", "-F"], check=True)
        subprocess.run(["iptables", "-X"], check=True)

        # Set default policies
        subprocess.run(["iptables", "-P", "INPUT", "DROP"], check=True)
        subprocess.run(["iptables", "-P", "FORWARD", "DROP"], check=True)
        subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)

        # Apply rules
        for rule in rules:
            if rule in self.required_ports:
                protocol = rule
                port = self.required_ports[protocol]
                subprocess.run([
                    "iptables", "-A", "INPUT",
                    "-p", "tcp",
                    "--dport", str(port),
                    "-j", "ACCEPT"
                ], check=True)
            else:
                # Custom rule, assume it's in the format "source:port"
                source, port = rule.split(":")
                subprocess.run([
                    "iptables", "-A", "INPUT",
                    "-p", "tcp",
                    "-s", source,
                    "--dport", port,
                    "-j", "ACCEPT"
                ], check=True)

    def _backup_rules(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = self.backup_dir / f"rules_{timestamp}.json"
        shutil.copy(self.rules_dir / "rules.json", backup_path)
        return backup_path

    def cleanup(self) -> bool:
        """Clean up firewall rules and configurations"""
        try:
            # Create backup before cleanup
            backup_path = self._backup_rules()
            
            # Reset iptables
            subprocess.run(["iptables", "-F"], check=True)
            subprocess.run(["iptables", "-X"], check=True)
            
            # Set default policies
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)
            
            # Stop and disable fail2ban
            subprocess.run(["systemctl", "stop", "fail2ban"], check=True)
            subprocess.run(["systemctl", "disable", "fail2ban"], check=True)
            
            self.logger.info("Firewall cleanup completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Firewall cleanup failed: {e}")
            return False