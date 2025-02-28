from ...core.base import BaseStep
import subprocess
import logging
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class KeycloakDeployStep(BaseStep):
    """Step for deploying Keycloak and its database"""
    
    def __init__(self):
        super().__init__("keycloak_deployment", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = [
            {
                'name': 'KEYCLOAK_ADMIN',
                'prompt': 'Enter Keycloak admin username',
                'default': 'admin'
            },
            {
                'name': 'KEYCLOAK_ADMIN_PASSWORD',
                'prompt': 'Enter Keycloak admin password',
                'default': None  # Requires user input
            },
            {
                'name': 'KEYCLOAK_PORT',
                'prompt': 'Enter Keycloak port',
                'default': '8443'
            },
            {
                'name': 'KEYCLOAK_DOMAIN',
                'prompt': 'Enter Keycloak domain name',
                'default': 'localhost'
            },
            {
                'name': 'DB_VENDOR',
                'prompt': 'Enter database vendor',
                'default': 'postgres'
            },
            {
                'name': 'DB_USER',
                'prompt': 'Enter database username',
                'default': 'keycloak'
            },
            {
                'name': 'DB_PASSWORD',
                'prompt': 'Enter database password',
                'default': None  # Requires user input
            },
            {
                'name': 'DB_DATABASE',
                'prompt': 'Enter database name',
                'default': 'keycloak'
            },
            {
                'name': 'DOCKER_NETWORK',
                'prompt': 'Enter Docker network name',
                'default': 'keycloak-network'
            },
            {
                'name': 'KEYCLOAK_VERSION',
                'prompt': 'Enter Keycloak version',
                'default': 'latest'
            }
        ]
    
    def _check_dependencies(self) -> bool:
        """Check if Docker is available and network exists"""
        try:
            # Check if docker command exists and is working
            docker_check = self._run_command(["docker", "info"], check=False)
            if docker_check.returncode != 0:
                self.logger.error("Docker is not running or not installed")
                return False
                
            # Check if Docker network exists
            network_name = os.environ.get('DOCKER_NETWORK', 'keycloak-network')
            network_check = self._run_command(
                ['docker', 'network', 'inspect', network_name],
                check=False
            )
            if network_check.returncode != 0:
                self.logger.error(f"Docker network '{network_name}' does not exist")
                return False
            
            # Check if Docker volumes exist
            volumes = ['keycloak-data', 'postgres-data']
            for volume in volumes:
                volume_check = self._run_command(
                    ['docker', 'volume', 'inspect', volume],
                    check=False
                )
                if volume_check.returncode != 0:
                    self.logger.error(f"Docker volume '{volume}' does not exist")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies (Docker should be installed by DockerSetupStep)"""
        self.logger.info("This step requires Docker setup step to be executed first")
        return False  # Cannot install Docker here, return False to abort
    
    def _wait_for_container(self, container_name: str, max_wait: int = 60) -> bool:
        """Wait for a container to be healthy"""
        self.logger.info(f"Waiting for {container_name} to be ready (max {max_wait} seconds)...")
        
        for i in range(max_wait):
            try:
                status = self._run_command(
                    ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container_name],
                    check=False
                )
                
                if status.returncode == 0 and status.stdout.strip() == 'healthy':
                    self.logger.info(f"{container_name} is ready")
                    return True
                
                time.sleep(1)
            except Exception as e:
                self.logger.warning(f"Error checking container status: {str(e)}")
                time.sleep(1)
                
        self.logger.error(f"{container_name} did not become healthy within {max_wait} seconds")
        return False
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Deploy Keycloak and PostgreSQL containers"""
        try:
            network_name = env_vars.get('DOCKER_NETWORK', 'keycloak-network')
            keycloak_version = env_vars.get('KEYCLOAK_VERSION', 'latest')
            keycloak_port = env_vars.get('KEYCLOAK_PORT', '8443')
            
            # 1. Deploy PostgreSQL container
            self.logger.info("Deploying PostgreSQL container...")
            pg_container_name = "keycloak-postgres"
            
            # Check if container already exists
            container_check = self._run_command(
                ['docker', 'ps', '-a', '--filter', f'name={pg_container_name}', '--format', '{{.Names}}'],
                check=False
            )
            
            if container_check.stdout.strip() == pg_container_name:
                # Stop and remove existing container
                self.logger.info(f"Container {pg_container_name} already exists. Stopping and removing...")
                self._run_command(['docker', 'stop', pg_container_name], check=False)
                self._run_command(['docker', 'rm', pg_container_name], check=False)
            
            # Start PostgreSQL container
            self._run_command([
                'docker', 'run', '-d',
                '--name', pg_container_name,
                '--network', network_name,
                '-v', 'postgres-data:/var/lib/postgresql/data',
                '-e', f"POSTGRES_DB={env_vars.get('DB_DATABASE', 'keycloak')}",
                '-e', f"POSTGRES_USER={env_vars.get('DB_USER', 'keycloak')}",
                '-e', f"POSTGRES_PASSWORD={env_vars['DB_PASSWORD']}",
                '--health-cmd', 'pg_isready -U postgres',
                '--health-interval', '10s',
                '--health-timeout', '5s',
                '--health-retries', '5',
                '--restart', 'unless-stopped',
                'postgres:13'
            ])
            
            # Wait for PostgreSQL to be healthy
            if not self._wait_for_container(pg_container_name, 60):
                self.logger.error("PostgreSQL container failed to start properly")
                return False
            
            # 2. Deploy Keycloak container
            self.logger.info("Deploying Keycloak container...")
            kc_container_name = "keycloak"
            
            # Check if container already exists
            container_check = self._run_command(
                ['docker', 'ps', '-a', '--filter', f'name={kc_container_name}', '--format', '{{.Names}}'],
                check=False
            )
            
            if container_check.stdout.strip() == kc_container_name:
                # Stop and remove existing container
                self.logger.info(f"Container {kc_container_name} already exists. Stopping and removing...")
                self._run_command(['docker', 'stop', kc_container_name], check=False)
                self._run_command(['docker', 'rm', kc_container_name], check=False)
            
            # Start Keycloak container
            self._run_command([
                'docker', 'run', '-d',
                '--name', kc_container_name,
                '--network', network_name,
                '-p', f"{keycloak_port}:8443",
                '-v', 'keycloak-data:/opt/keycloak/data',
                '-e', f"KEYCLOAK_ADMIN={env_vars.get('KEYCLOAK_ADMIN', 'admin')}",
                '-e', f"KEYCLOAK_ADMIN_PASSWORD={env_vars['KEYCLOAK_ADMIN_PASSWORD']}",
                '-e', 'DB_VENDOR=postgres',
                '-e', f"DB_ADDR={pg_container_name}",
                '-e', f"DB_DATABASE={env_vars.get('DB_DATABASE', 'keycloak')}",
                '-e', f"DB_USER={env_vars.get('DB_USER', 'keycloak')}",
                '-e', f"DB_PASSWORD={env_vars['DB_PASSWORD']}",
                '-e', f"KC_HOSTNAME={env_vars.get('KEYCLOAK_DOMAIN', 'localhost')}",
                '-e', 'KC_HTTPS_CERTIFICATE_FILE=/opt/keycloak/conf/server.crt.pem',
                '-e', 'KC_HTTPS_CERTIFICATE_KEY_FILE=/opt/keycloak/conf/server.key.pem',
                '--health-cmd', 'curl -f http://localhost:8080/health/ready || exit 1',
                '--health-interval', '30s',
                '--health-timeout', '10s',
                '--health-retries', '3',
                '--restart', 'unless-stopped',
                f"quay.io/keycloak/keycloak:{keycloak_version}",
                'start-dev'
            ])
            
            # Wait for Keycloak to be healthy
            if not self._wait_for_container(kc_container_name, 120):
                self.logger.error("Keycloak container failed to start properly")
                return False
            
            self.logger.info(f"Keycloak deployed successfully, accessible at https://{env_vars.get('KEYCLOAK_DOMAIN', 'localhost')}:{keycloak_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy Keycloak: {str(e)}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up on failure - stop containers but preserve data volumes"""
        try:
            containers = ['keycloak', 'keycloak-postgres']
            for container in containers:
                try:
                    # Check if container exists
                    container_check = self._run_command(
                        ['docker', 'ps', '-a', '--filter', f'name={container}', '--format', '{{.Names}}'],
                        check=False
                    )
                    
                    if container_check.stdout.strip() == container:
                        self.logger.info(f"Stopping and removing container: {container}")
                        self._run_command(['docker', 'stop', container], check=False)
                        self._run_command(['docker', 'rm', container], check=False)
                except Exception as e:
                    self.logger.warning(f"Error cleaning up container {container}: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")