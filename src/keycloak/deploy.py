from ..deployment.base import DeploymentStep
import docker

class KeycloakDeploymentStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("keycloak_deployment", can_cleanup=True)
        self.config = config
        self.client = docker.from_env()

    def check_completed(self) -> bool:
        try:
            container = self.client.containers.get("keycloak")
            return container.status == "running"
        except docker.errors.NotFound:
            return False

    def execute(self) -> bool:
        try:
            # Pull required images
            self.client.images.pull("postgres:15")
            self.client.images.pull("quay.io/keycloak/keycloak:latest")

            # Start PostgreSQL
            postgres_container = self.client.containers.run(
                "postgres:15",
                name="postgres",
                environment={
                    "POSTGRES_DB": self.config["db_name"],
                    "POSTGRES_USER": self.config["db_user"],
                    "POSTGRES_PASSWORD": self.config["db_password"]
                },
                network="keycloak-network",
                detach=True
            )

            # Wait for PostgreSQL to be ready
            postgres_container.exec_run(
                "until pg_isready; do sleep 1; done",
                tty=True
            )

            # Start Keycloak
            self.client.containers.run(
                "quay.io/keycloak/keycloak:latest",
                name="keycloak",
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
                },
                ports={
                    '8080/tcp': 8080,
                    '8443/tcp': 8443
                },
                network="keycloak-network",
                detach=True
            )

            return True
        except Exception as e:
            self.logger.error(f"Failed to deploy Keycloak: {e}")
            self.cleanup()
            return False

    def cleanup(self) -> bool:
        try:
            # Stop and remove containers
            for container_name in ["keycloak", "postgres"]:
                try:
                    container = self.client.containers.get(container_name)
                    container.stop()
                    container.remove()
                except docker.errors.NotFound:
                    pass

            # Remove volumes
            for volume in self.client.volumes.list():
                if volume.name.startswith(("keycloak_", "postgres_")):
                    volume.remove()

            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Keycloak deployment: {e}")
            return False