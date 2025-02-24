from ..deployment.base import DeploymentStep
import subprocess
import logging

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
        """Prepare the system by installing required packages"""
        try:
            # Check and install dependencies
            for pkg in self.packages:
                if not self._is_package_installed(pkg):
                    self._install_package(pkg)

            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to prepare system: {e}")
            return False

    def _is_package_installed(self, package: str) -> bool:
        """Check if a package is installed"""
        result = subprocess.run(
            ["dpkg", "-l", package],
            capture_output=True,
            text=True
        )
        return "ii" in result.stdout

    def _install_package(self, package: str) -> None:
        """Install a package using apt-get"""
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", package], check=True)
        logging.info(f"Installed package: {package}")
