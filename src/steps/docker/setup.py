from ...core.base import BaseStep
import json
import os
from pathlib import Path
from typing import Dict

# Import step-specific modules
from .dependencies import check_docker_dependencies, install_docker_dependencies
from .environment import get_required_variables, validate_variables

class DockerSetupStep(BaseStep):
    """Step for setting up Docker and related resources"""
    
    def __init__(self):
        super().__init__("docker_setup", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if Docker is installed and running"""
        return check_docker_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install Docker and Docker Compose"""
        return install_docker_dependencies()
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Create Docker network and volumes"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Get configuration variables
            network_name = env_vars.get('DOCKER_NETWORK', 'keycloak-network')
            network_subnet = env_vars.get('DOCKER_NETWORK_SUBNET', '172.20.0.0/16')
            
            # Check if network already exists
            network_check = self._run_command(
                ['docker', 'network', 'inspect', network_name], 
                check=False
            )
            
            if network_check.returncode != 0:
                # Create network if it doesn't exist
                self._run_command([
                    'docker', 'network', 'create',
                    '--subnet', network_subnet,
                    '--driver', 'bridge',
                    network_name
                ])
                self.logger.info(f"Created Docker network: {network_name}")
            else:
                self.logger.info(f"Docker network {network_name} already exists")
            
            # Create required volumes
            volumes = ['keycloak-data', 'postgres-data']
            for volume in volumes:
                volume_check = self._run_command(
                    ['docker', 'volume', 'inspect', volume],
                    check=False
                )
                
                if volume_check.returncode != 0:
                    # Create volume if it doesn't exist
                    self._run_command(['docker', 'volume', 'create', volume])
                    self.logger.info(f"Created Docker volume: {volume}")
                else:
                    self.logger.info(f"Docker volume {volume} already exists")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to set up Docker resources: {str(e)}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up Docker resources on failure"""
        try:
            # Don't remove volumes to avoid data loss
            # Only remove the network if we created it
            network_name = os.environ.get('DOCKER_NETWORK', 'keycloak-network')
            
            # Check if the network was just created (no containers attached)
            try:
                network_info = json.loads(
                    self._run_command(
                        ['docker', 'network', 'inspect', network_name],
                        check=False
                    ).stdout
                )
                
                if network_info and 'Containers' in network_info[0]:
                    if not network_info[0]['Containers']:
                        # No containers attached, safe to remove
                        self._run_command(['docker', 'network', 'rm', network_name], check=False)
                        self.logger.info(f"Removed Docker network: {network_name}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up network: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")