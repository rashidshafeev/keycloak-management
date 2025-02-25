import os
import subprocess
import logging
import platform
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class DependencyManager:
    def __init__(self):
        self.is_debian = self._is_debian_based()
        self.is_container = self._is_in_container()

    def _is_debian_based(self) -> bool:
        """Check if the system is Debian-based"""
        return os.path.exists('/etc/debian_version')

    def _is_in_container(self) -> bool:
        """Check if running inside a container"""
        return os.path.exists('/.dockerenv') or any('docker' in line for line in open('/proc/1/cgroup', 'r').readlines())

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        try:
            return subprocess.run(command, check=check, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output: {e.stderr}")
            if check:
                raise

    def check_docker(self) -> Tuple[bool, str]:
        """Check if Docker is installed and running"""
        try:
            # Check if docker command exists
            self._run_command(["docker", "--version"], check=True)
            # Check if docker daemon is running (not needed inside container)
            if not self.is_container:
                self._run_command(["docker", "info"], check=True)
            return True, "Docker is installed"
        except subprocess.CalledProcessError:
            return False, "Docker is not running"
        except FileNotFoundError:
            return False, "Docker is not installed"

    def install_docker(self) -> bool:
        """Install Docker"""
        try:
            # Remove old Docker packages if they exist
            old_packages = ['docker.io', 'docker-doc', 'docker-compose', 'podman-docker', 'containerd', 'runc']
            for pkg in old_packages:
                self._run_command(['apt-get', 'remove', '-y', pkg], check=False)

            # Install dependencies for Docker repository
            self._run_command(['apt-get', 'update'])
            self._run_command(['apt-get', 'install', '-y',
                             'ca-certificates',
                             'curl',
                             'gnupg'])

            # Add Docker's official GPG key
            keyring_dir = '/etc/apt/keyrings'
            if not os.path.exists(keyring_dir):
                os.makedirs(keyring_dir)
            
            self._run_command([
                'curl', '-fsSL',
                'https://download.docker.com/linux/debian/gpg',
                '-o', '/etc/apt/keyrings/docker.asc'
            ])

            # Add Docker repository
            with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
                f.write(
                    f"deb [arch={subprocess.check_output(['dpkg', '--print-architecture']).decode().strip()} "
                    f"signed-by=/etc/apt/keyrings/docker.asc] "
                    f"https://download.docker.com/linux/debian "
                    f"{subprocess.check_output(['lsb_release', '-cs']).decode().strip()} stable"
                )

            # Install Docker
            self._run_command(['apt-get', 'update'])
            self._run_command(['apt-get', 'install', '-y',
                             'docker-ce',
                             'docker-ce-cli',
                             'containerd.io',
                             'docker-buildx-plugin',
                             'docker-compose-plugin'])

            # Start and enable Docker service (not needed inside container)
            if not self.is_container:
                self._run_command(['systemctl', 'start', 'docker'])
                self._run_command(['systemctl', 'enable', 'docker'])

            return True
        except Exception as e:
            logger.error(f"Failed to install Docker: {str(e)}")
            return False

    def check_and_install_system_packages(self) -> bool:
        """Check and install required system packages"""
        if not self.is_debian:
            logger.warning("Non-Debian system detected. Package installation may not work.")
            return False

        required_packages = {
            'base': [
                'curl',
                'wget',
                'git',
                'build-essential',
                'python3-dev',
                'python3-pip',
                'python3-venv',
                'libssl-dev',
                'libffi-dev',
            ],
            'security': [
                'iptables',
                'ufw',
            ],
            'docker': [
                'docker-ce-cli'  # Only Docker client inside container
            ]
        }

        try:
            # Update package list
            self._run_command(['apt-get', 'update'])
            
            # Install packages
            all_packages = []
            for category, packages in required_packages.items():
                all_packages.extend(packages)
            
            self._run_command(['apt-get', 'install', '-y'] + all_packages)
            
            # Install Docker if needed
            docker_ok, _ = self.check_docker()
            if not docker_ok:
                if not self.install_docker():
                    return False

            return True
        except Exception as e:
            logger.error(f"Failed to install system packages: {str(e)}")
            return False

    def check_requirements(self) -> List[str]:
        """Check all requirements and return list of issues"""
        issues = []

        # Check Docker
        docker_ok, docker_msg = self.check_docker()
        if not docker_ok:
            issues.append(f"Docker issue: {docker_msg}")

        return issues

    def setup_all(self) -> bool:
        """Set up all dependencies"""
        # First check requirements
        issues = self.check_requirements()
        if issues:
            logger.info("Found missing dependencies, attempting to install...")
            
        # Install all required packages
        if not self.check_and_install_system_packages():
            logger.error("Failed to install required packages")
            return False

        # Verify installation
        issues = self.check_requirements()
        if issues:
            logger.error("Dependencies still missing after installation:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        return True
