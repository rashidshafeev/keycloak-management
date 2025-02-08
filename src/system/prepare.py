from ..deployment.base import DeploymentStep
import subprocess

class SystemPreparationStep(DeploymentStep):
    def __init__(self):
        super().__init__("system_preparation", can_cleanup=False)
        self.packages = [
            "apt-transport-https",
            "ca-certificates",
            "curl",
            "gnupg"
        ]

    def check_completed(self) -> bool:
        try:
            for pkg in self.packages:
                result = subprocess.run(
                    ["dpkg", "-l", pkg],
                    capture_output=True,
                    text=True
                )
                if "ii" not in result.stdout:
                    return False
            return True
        except Exception:
            return False

    def execute(self) -> bool:
        try:
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y"] + self.packages, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to prepare system: {e}")
            return False