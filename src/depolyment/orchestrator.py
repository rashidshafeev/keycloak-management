from pathlib import Path
import logging
from ..utils.logger import setup_logging
from ..system.prepare import SystemPreparationStep
from ..system.docker import DockerSetupStep
from ..system.firewall import FirewallSetupStep
from ..security.ssl import CertificateManager
from ..keycloak.deploy import KeycloakDeploymentStep
from .base import DeploymentStep

class DeploymentOrchestrator:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger("keycloak_deployer")
        self.steps = [
            SystemPreparationStep(),
            FirewallSetupStep(self.config),
            DockerSetupStep(),
            CertificateManager(self.config),
            KeycloakDeploymentStep(self.config)
        ]

    def _load_config(self, config_path: Path) -> dict:
        return json.loads(config_path.read_text())

    @contextmanager
    def step_context(self, step: DeploymentStep):
        try:
            yield
        except Exception as e:
            self.logger.error(f"Step {step.name} failed: {e}")
            if step.can_cleanup:
                step.cleanup()
            raise

    def deploy(self) -> bool:
        for step in self.steps:
            if step.can_skip and step.check_completed():
                self.logger.info(f"Step {step.name} already completed, skipping...")
                continue

            self.logger.info(f"Executing step: {step.name}")
            with self.step_context(step):
                if not step.execute():
                    return False

        return True