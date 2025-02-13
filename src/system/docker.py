from ..deployment.base import DeploymentStep
import docker
import subprocess
import logging
from typing import List, Dict

class DockerSetupStep(DeploymentStep):
    def __init__(self):
        super().__init__("docker_setup", can_cleanup=True)
        self.client = docker.from_env()
        self.logger = logging.getLogger(__name__)
        
        # Define required volumes
        self.volumes = {
            "keycloak-data": {
                "name": "keycloak-data",
                "labels": {"app": "keycloak", "component": "server"}
            },
            "postgres-data": {
                "name": "postgres-data",
                "labels": {"app": "keycloak", "component": "database"}
            }
        }
        
        # Define network configuration
        self.network_config = {
            "name": "keycloak-network",
            "driver": "bridge",
            "labels": {"app": "keycloak"},
            "ipam": {
                "driver": "default",
                "config": [{"subnet": "172.20.0.0/16"}]
            },
            "options": {
                "com.docker.network.bridge.name": "keycloak-br0",
                "com.docker.network.bridge.enable_icc": "true",
                "com.docker.network.bridge.enable_ip_masquerade": "true"
            }
        }

    def check_completed(self) -> bool:
        """Check if Docker is running and required resources exist"""
        try:
            # Check Docker daemon
            if not self.client.ping():
                return False
                
            # Check network
            try:
                self.client.networks.get(self.network_config["name"])
            except docker.errors.NotFound:
                return False
                
            # Check volumes
            for volume in self.volumes.values():
                try:
                    self.client.volumes.get(volume["name"])
                except docker.errors.NotFound:
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Failed to check Docker setup: {e}")
            return False

    def execute(self) -> bool:
        """Set up Docker environment with network and volumes"""
        try:
            # Ensure Docker is installed and running
            if not self._ensure_docker_running():
                return False

            # Create network if doesn't exist
            try:
                self.client.networks.get(self.network_config["name"])
                self.logger.info(f"Network {self.network_config['name']} already exists")
            except docker.errors.NotFound:
                self.logger.info(f"Creating network {self.network_config['name']}")
                self.client.networks.create(
                    self.network_config["name"],
                    driver=self.network_config["driver"],
                    ipam=self.network_config["ipam"],
                    options=self.network_config["options"],
                    labels=self.network_config["labels"]
                )

            # Create volumes if they don't exist
            for volume_config in self.volumes.values():
                try:
                    self.client.volumes.get(volume_config["name"])
                    self.logger.info(f"Volume {volume_config['name']} already exists")
                except docker.errors.NotFound:
                    self.logger.info(f"Creating volume {volume_config['name']}")
                    self.client.volumes.create(
                        name=volume_config["name"],
                        labels=volume_config["labels"]
                    )

            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Docker: {e}")
            return False

    def _ensure_docker_running(self) -> bool:
        """Ensure Docker is installed and running"""
        try:
            if not self.check_completed():
                # Install Docker if needed
                subprocess.run([
                    "curl", "-fsSL", 
                    "https://get.docker.com", "-o", "get-docker.sh"
                ], check=True)
                subprocess.run(["sh", "get-docker.sh"], check=True)
                
                # Start and enable Docker service
                subprocess.run(["systemctl", "start", "docker"], check=True)
                subprocess.run(["systemctl", "enable", "docker"], check=True)
                
                # Verify Docker is running
                if not self.client.ping():
                    raise Exception("Docker daemon not responding after installation")
                    
            return True
        except Exception as e:
            self.logger.error(f"Failed to ensure Docker is running: {e}")
            return False

    def cleanup(self) -> bool:
        """Clean up Docker resources"""
        try:
            # Remove volumes
            for volume_config in self.volumes.values():
                try:
                    volume = self.client.volumes.get(volume_config["name"])
                    self.logger.info(f"Removing volume {volume_config['name']}")
                    volume.remove()
                except docker.errors.NotFound:
                    pass

            # Remove network
            try:
                network = self.client.networks.get(self.network_config["name"])
                self.logger.info(f"Removing network {self.network_config['name']}")
                network.remove()
            except docker.errors.NotFound:
                pass

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Docker resources: {e}")
            return False