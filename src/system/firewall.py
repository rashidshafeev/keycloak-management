from ..deployment.base import DeploymentStep
import subprocess

class FirewallSetupStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("firewall_setup", can_cleanup=True)
        self.config = config

    def check_completed(self) -> bool:
        try:
            result = subprocess.run(
                ["ufw", "status"], 
                capture_output=True, 
                text=True
            )
            return "Status: active" in result.stdout
        except Exception:
            return False

    def execute(self) -> bool:
        try:
            # Reset firewall to default state
            subprocess.run(["ufw", "--force", "reset"], check=True)
            
            # Default policies
            subprocess.run(["ufw", "default", "deny", "incoming"], check=True)
            subprocess.run(["ufw", "default", "allow", "outgoing"], check=True)
            
            # Allow configured ports
            for port in self.config["system"]["firewall"]["allowed_ports"]:
                subprocess.run(["ufw", "allow", str(port)], check=True)
            
            # Allow admin IPs for Keycloak admin console
            for ip in self.config["system"]["firewall"]["admin_allowed_ips"]:
                subprocess.run([
                    "ufw", "allow", "from", ip, "to", "any", "port", "8443"
                ], check=True)
            
            # Enable firewall
            subprocess.run(["ufw", "--force", "enable"], check=True)
            
            # Setup fail2ban
            subprocess.run(["systemctl", "enable", "fail2ban"], check=True)
            subprocess.run(["systemctl", "start", "fail2ban"], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup firewall: {e}")
            return False

    def cleanup(self) -> bool:
        try:
            # Disable firewall
            subprocess.run(["ufw", "--force", "disable"], check=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup firewall: {e}")
            return False