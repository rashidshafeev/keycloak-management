import os
import subprocess
import sys
import logging
from typing import List, Dict
from pathlib import Path

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

    def install_system_packages(self) -> bool:
        """Install required system packages"""
        if not self.is_debian:
            logger.warning("Non-Debian system detected. Package installation may not work.")
            return False

        packages = [
            'curl',
            'wget',
            'git',
            'build-essential',
            'python3-dev',
            'python3-pip',
            'python3-venv',
            'libssl-dev',
            'libffi-dev',
            'iptables',
            'ufw'
        ]

        try:
            # Update package list
            self._run_command(['apt-get', 'update'])
            
            # Install packages
            self._run_command(['apt-get', 'install', '-y'] + packages)
            
            return True
        except Exception as e:
            logger.error(f"Failed to install system packages: {str(e)}")
            return False

    def install_docker(self) -> bool:
        """Install Docker if not in container"""
        if self.is_container:
            logger.info("Running in container, skipping Docker installation")
            return True

        try:
            # Check if Docker is already installed
            if self._run_command(['docker', '--version'], check=False).returncode == 0:
                logger.info("Docker is already installed")
                return True

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

            # Start and enable Docker service
            self._run_command(['systemctl', 'start', 'docker'])
            self._run_command(['systemctl', 'enable', 'docker'])

            # Configure Docker network
            self._run_command(['docker', 'network', 'create', 'keycloak-network'])

            return True
        except Exception as e:
            logger.error(f"Failed to install Docker: {str(e)}")
            return False

    def configure_firewall(self) -> bool:
        """Configure firewall rules"""
        try:
            # Check if UFW is installed
            if self._run_command(['which', 'ufw'], check=False).returncode != 0:
                logger.error("UFW is not installed")
                return False

            # Allow necessary ports
            ports = ['80/tcp', '443/tcp', '8080/tcp', '8443/tcp']
            for port in ports:
                self._run_command(['ufw', 'allow', port])

            # Configure Docker rules
            docker_rules = """
[Docker]
title=Docker
description=Docker container engine
ports=2375,2376,2377,7946/tcp|7946/udp|4789/udp
"""
            docker_rules_file = Path('/etc/ufw/applications.d/docker')
            docker_rules_file.write_text(docker_rules)

            # Reload UFW
            self._run_command(['ufw', 'reload'])

            return True
        except Exception as e:
            logger.error(f"Failed to configure firewall: {str(e)}")
            return False

    def setup_all(self) -> bool:
        """Set up all dependencies"""
        success = True
        
        # Install system packages
        logger.info("Installing system packages...")
        if not self.install_system_packages():
            success = False
            logger.error("Failed to install system packages")

        # Install Docker if needed
        if not self.is_container:
            logger.info("Installing Docker...")
            if not self.install_docker():
                success = False
                logger.error("Failed to install Docker")

        # Configure firewall
        logger.info("Configuring firewall...")
        if not self.configure_firewall():
            success = False
            logger.error("Failed to configure firewall")

        return success
