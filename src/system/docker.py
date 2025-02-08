from ..deployment.base import DeploymentStep
import docker
import subprocess

class DockerSetupStep(DeploymentStep):
    def __init__(self):
        super().__init__("docker_setup", can_cleanup=True)
        self.client = docker.from_env()

    def check_completed(self) -> bool:
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def execute(self) -> bool:
        try:
            if not self.check_completed():
                subprocess.run([
                    "curl", "-fsSL", 
                    "https://get.docker.com", "-o", "get-docker.sh"
                ], check=True)
                subprocess.run(["sh", "get-docker.sh"], check=True)
                subprocess.run(["systemctl", "start", "docker"], check=True)
                subprocess.run(["systemctl", "enable", "docker"], check=True)

            # Create network if doesn't exist
            try:
                self.client.networks.get("keycloak-network")
            except docker.errors.NotFound:
                self.client.networks.create("keycloak-network")

            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Docker: {e}")
            return False

    def cleanup(self) -> bool:
        try:
            # Remove Docker network
            try:
                network = self.client.networks.get("keycloak-network")
                network.remove()
            except docker.errors.NotFound:
                pass

            # Stop Docker service
            subprocess.run(["systemctl", "stop", "docker"], check=True)
            subprocess.run(["systemctl", "disable", "docker"], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Docker: {e}")
            return False