
from ..deployment.base import DeploymentStep
import docker
import logging
import time
from typing import Optional
import requests
from requests.exceptions import RequestException

class KeycloakDeploymentStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("keycloak_deployment", can_cleanup=True)
        self.config = config
        self.client = docker.from_env()
        self.logger = logging.getLogger(__name__)
        
        # Container configurations
        self.postgres_config = {
            "image": "postgres:15",
            "name": "postgres",
            "hostname": "postgres",
            "volumes": {
                "postgres-data": {"bind": "/var/lib/postgresql/data", "mode": "rw"}
            },
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U postgres"],
                "interval": 10000000000,  # 10s
                "timeout": 5000000000,    # 5s
                "retries": 5
            },
            "restart_policy": {"Name": "unless-stopped"},
            "resources": {
                "cpu_shares": 2,
                "mem_limit": "1g",
                "mem_reservation": "512m"
            }
        }
        
        self.keycloak_config = {
            "image": "quay.io/keycloak/keycloak:latest",
            "name": "keycloak",
            "hostname": "keycloak",
            "volumes": {
                "keycloak-data": {"bind": "/opt/keycloak/data", "mode": "rw"}
            },
            "healthcheck": {
                "test": ["CMD", "curl", "-f", "http://localhost:8080/health/ready"],
                "interval": 30000000000,  # 30s
                "timeout": 10000000000,   # 10s
                "retries": 3
            },
            "restart_policy": {"Name": "unless-stopped"},
            "resources": {
                "cpu_shares": 4,
                "mem_limit": "2g",
                "mem_reservation": "1g"
            }
        }

    def check_completed(self) -> bool:
        """Check if Keycloak is running and healthy"""
        try:
            # Check both containers
            postgres = self.client.containers.get("postgres")
            keycloak = self.client.containers.get("keycloak")
            
            # Check container states
            if postgres.status != "running" or keycloak.status != "running":
                return False
                
            # Check container health
            postgres_health = postgres.attrs['State'].get('Health', {}).get('Status')
            keycloak_health = keycloak.attrs['State'].get('Health', {}).get('Status')
            
            return postgres_health == "healthy" and keycloak_health == "healthy"
        except docker.errors.NotFound:
            return False
        except Exception as e:
            self.logger.error(f"Failed to check deployment status: {e}")
            return False

    def execute(self) -> bool:
        """Deploy Keycloak with PostgreSQL backend"""
        try:
            # Pull required images
            self.logger.info("Pulling required images...")
            self.client.images.pull(self.postgres_config["image"])
            self.client.images.pull(self.keycloak_config["image"])

            # Start PostgreSQL
            self.logger.info("Starting PostgreSQL...")
            postgres_container = self.client.containers.run(
                self.postgres_config["image"],
                name=self.postgres_config["name"],
                hostname=self.postgres_config["hostname"],
                environment={
                    "POSTGRES_DB": self.config["db_name"],
                    "POSTGRES_USER": self.config["db_user"],
                    "POSTGRES_PASSWORD": self.config["db_password"]
                },
                volumes=self.postgres_config["volumes"],
                healthcheck=self.postgres_config["healthcheck"],
                restart_policy=self.postgres_config["restart_policy"],
                cpu_shares=self.postgres_config["resources"]["cpu_shares"],
                mem_limit=self.postgres_config["resources"]["mem_limit"],
                mem_reservation=self.postgres_config["resources"]["mem_reservation"],
                network="keycloak-network",
                detach=True
            )

            # Wait for PostgreSQL to be healthy
            self.logger.info("Waiting for PostgreSQL to be healthy...")
            if not self._wait_for_container_health(postgres_container):
                raise Exception("PostgreSQL failed to become healthy")

            # Start Keycloak
            self.logger.info("Starting Keycloak...")
            keycloak_container = self.client.containers.run(
                self.keycloak_config["image"],
                name=self.keycloak_config["name"],
                hostname=self.keycloak_config["hostname"],
                environment={
                    "DB_VENDOR": "postgres",
                    "DB_ADDR": "postgres",
                    "DB_DATABASE": self.config["db_name"],
                    "DB_USER": self.config["db_user"],
                    "DB_PASSWORD": self.config["db_password"],
                    "KEYCLOAK_ADMIN": self.config["admin_user"],
                    "KEYCLOAK_ADMIN_PASSWORD": self.config["admin_password"],
                    # Event configuration
                    "KC_SPI_EVENTS_LISTENER": "jboss-logging,http-webhook",
                    "KC_EVENT_STORE_PROVIDER": "jpa",
                    "KC_EVENT_STORE_EXPIRATION": str(self.config.get("events", {}).get("storage", {}).get("expiration", 2592000)),
                    "KC_EVENT_ADMIN": "true",
                    "KC_EVENT_ADMIN_INCLUDE_REPRESENTATION": "false",
                    # Webhook configuration
                    "KC_SPI_EVENTS_LISTENER_HTTP_WEBHOOK_URL": self.config.get("events", {}).get("listeners", [])[2].get("properties", {}).get("url", "http://event-bus:3000/events"),
                    "KC_SPI_EVENTS_LISTENER_HTTP_WEBHOOK_SECRET": self.config.get("events", {}).get("listeners", [])[2].get("properties", {}).get("secret", "${EVENT_WEBHOOK_SECRET}"),
                    # Performance tuning
                    "KC_HTTP_RELATIVE_PATH": "/auth",
                    "KC_PROXY": "edge",
                    "KC_HOSTNAME_STRICT": "false",
                    "KC_HTTP_MAX_CONNECTIONS": "100"
                },
                volumes=self.keycloak_config["volumes"],
                healthcheck=self.keycloak_config["healthcheck"],
                restart_policy=self.keycloak_config["restart_policy"],
                cpu_shares=self.keycloak_config["resources"]["cpu_shares"],
                mem_limit=self.keycloak_config["resources"]["mem_limit"],
                mem_reservation=self.keycloak_config["resources"]["mem_reservation"],
                ports={
                    '8080/tcp': 8080,
                    '8443/tcp': 8443
                },
                network="keycloak-network",
                detach=True
            )

            # Wait for Keycloak to be healthy
            self.logger.info("Waiting for Keycloak to be healthy...")
            if not self._wait_for_container_health(keycloak_container):
                raise Exception("Keycloak failed to become healthy")

            # Verify Keycloak is responding
            self.logger.info("Verifying Keycloak deployment...")
            if not self._verify_keycloak_running():
                raise Exception("Keycloak is not responding")

            self.logger.info("Keycloak deployment completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to deploy Keycloak: {e}")
            self.cleanup()
            return False

    def _wait_for_container_health(self, container, timeout: int = 180) -> bool:
        """Wait for container to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()  # Get latest state
            health = container.attrs['State'].get('Health', {})
            status = health.get('Status')
            
            if status == 'healthy':
                return True
            elif status == 'unhealthy':
                self.logger.error(f"Container {container.name} is unhealthy: {health.get('Log', [])}")
                return False
                
            time.sleep(5)
            
        self.logger.error(f"Container {container.name} failed to become healthy within {timeout} seconds")
        return False

    def _verify_keycloak_running(self, timeout: int = 30) -> bool:
        """Verify Keycloak is responding to requests"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8080/auth/health/ready")
                if response.status_code == 200:
                    return True
            except RequestException:
                pass
            time.sleep(5)
            
        return False

    def cleanup(self) -> bool:
        """Clean up deployment resources"""
        try:
            # Stop and remove containers
            for container_name in [self.keycloak_config["name"], self.postgres_config["name"]]:
                try:
                    container = self.client.containers.get(container_name)
                    self.logger.info(f"Stopping container {container_name}...")
                    container.stop(timeout=30)  # Give 30s for graceful shutdown
                    self.logger.info(f"Removing container {container_name}...")
                    container.remove()
                except docker.errors.NotFound:
                    pass

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Keycloak deployment: {e}")
            return False