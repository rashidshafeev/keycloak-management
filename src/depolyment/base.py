import logging
from abc import ABC, abstractmethod

class DeploymentStep(ABC):
    def __init__(self, name: str, can_cleanup: bool = True, can_skip: bool = True):
        self.name = name
        self.can_cleanup = can_cleanup
        self.can_skip = can_skip
        self.logger = logging.getLogger(f"keycloak_deployer.{name}")

    @abstractmethod
    def check_completed(self) -> bool:
        """Check if this step was already completed successfully"""
        pass

    @abstractmethod
    def execute(self) -> bool:
        """Execute the deployment step"""
        pass

    def cleanup(self) -> bool:
        """Clean up after failed execution"""
        if not self.can_cleanup:
            self.logger.warning(f"Cleanup not supported for {self.name}")
            return False
        raise NotImplementedError