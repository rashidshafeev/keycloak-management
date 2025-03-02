from ...core.base import BaseStep
import os
import subprocess
import time
import json
import requests
from requests.exceptions import RequestException
from pathlib import Path
from typing import Dict, Optional, List

# Import step-specific modules
from .dependencies import (
    check_keycloak_deployment_dependencies, install_keycloak_deployment_dependencies,
    check_docker_images, pull_docker_images
)
from .environment import get_required_variables, validate_variables
from .config_loader import ConfigLoader

class KeycloakDeploymentstep(BaseStep):
    """Step for Keycloak server deployment and configuration"""
    
    def __init__(self):
        super().__init__("keycloak_deployment", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_keycloak_deployment_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_keycloak_deployment_dependencies()
    
    def _prepare_container_configs(self, env_vars: Dict[str, str]) -> Dict:
        """
        Prepare container configurations
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            Dict: Dictionary of container configurations
        """
        # Initialize container configurations
        postgres_config = {
            "image": env_vars.get('POSTGRES_IMAGE', 'postgres:15'),
            "name": "postgres",
            "hostname": "postgres",
            "volumes": {
                env_vars.get('POSTGRES_DATA_DIR', '/opt/fawz/keycloak/postgres-data'): {
                    "bind": "/var/lib/postgresql/data", 
                    "mode": "rw"
                }
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
                "mem_limit": env_vars.get('POSTGRES_MEM_LIMIT', '1g'),
                "mem_reservation": env_vars.get('POSTGRES_MEM_RESERVATION', '512m')
            }
        }
        
        keycloak_config = {
            "image": env_vars.get('KEYCLOAK_IMAGE', 'quay.io/keycloak/keycloak:latest'),
            "name": "keycloak",
            "hostname": "keycloak",
            "volumes": {
                env_vars.get('KEYCLOAK_DATA_DIR', '/opt/fawz/keycloak/data'): {
                    "bind": "/opt/keycloak/data", 
                    "mode": "rw"
                }
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
                "mem_limit": env_vars.get('KEYCLOAK_MEM_LIMIT', '2g'),
                "mem_reservation": env_vars.get('KEYCLOAK_MEM_RESERVATION', '1g')
            }
        }
        
        return {
            "postgres": postgres_config,
            "keycloak": keycloak_config
        }
    
    def _prepare_keycloak_environment(self, env_vars: Dict[str, str]) -> Dict:
        """
        Prepare Keycloak environment variables
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            Dict: Dictionary of Keycloak environment variables
        """
        return {
            "DB_VENDOR": "postgres",
            "DB_ADDR": "postgres",
            "DB_DATABASE": env_vars.get('DB_NAME', 'keycloak'),
            "DB_USER": env_vars.get('DB_USER', 'keycloak'),
            "DB_PASSWORD": env_vars.get('DB_PASSWORD'),
            "KEYCLOAK_ADMIN": env_vars.get('KEYCLOAK_ADMIN', 'admin'),
            "KEYCLOAK_ADMIN_PASSWORD": env_vars.get('KEYCLOAK_ADMIN_PASSWORD'),
            # Frontend configuration
            "KC_HOSTNAME": env_vars.get('KEYCLOAK_DOMAIN', 'localhost'),
            "KC_HOSTNAME_URL": env_vars.get('KEYCLOAK_FRONTEND_URL', 'http://localhost:8080/auth'),
            # Event configuration
            "KC_SPI_EVENTS_LISTENER": "jboss-logging,http-webhook",
            "KC_EVENT_STORE_PROVIDER": "jpa",
            "KC_EVENT_STORE_EXPIRATION": env_vars.get('EVENT_STORAGE_EXPIRATION', '2592000'),
            "KC_EVENT_ADMIN": "true",
            "KC_EVENT_ADMIN_INCLUDE_REPRESENTATION": "false",
            # Webhook configuration
            "KC_SPI_EVENTS_LISTENER_HTTP_WEBHOOK_URL": env_vars.get('EVENT_WEBHOOK_URL', 'http://event-bus:3000/events'),
            "KC_SPI_EVENTS_LISTENER_HTTP_WEBHOOK_SECRET": env_vars.get('EVENT_WEBHOOK_SECRET', ''),
            # Performance tuning
            "KC_HTTP_RELATIVE_PATH": "/auth",
            "KC_PROXY": "edge",
            "KC_HOSTNAME_STRICT": "false",
            "KC_HTTP_MAX_CONNECTIONS": "100",
            # Features
            "KC_FEATURES": "token-exchange,admin-fine-grained-authz",
            # Start options
            "KC_LOG_LEVEL": env_vars.get('KEYCLOAK_LOG_LEVEL', 'INFO'),
            "KC_TRANSACTION_XA_ENABLED": "false",
            "JAVA_OPTS_APPEND": "-XX:MaxRAMPercentage=75.0"
        }
    
    def check_deployment_ready(self, env_vars: Dict[str, str], timeout: int = 300) -> bool:
        """
        Check if Keycloak and PostgreSQL are running and healthy
        
        Args:
            env_vars: Dictionary of environment variables
            timeout: Timeout in seconds
            
        Returns:
            bool: True if the deployment is ready, False otherwise
        """
        try:
            # Import docker here to ensure it's only used when needed
            import docker
            client = docker.from_env()
            
            # Check deployment status
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Check PostgreSQL container
                    try:
                        postgres = client.containers.get("postgres")
                        if postgres.status != "running":
                            self.logger.info("PostgreSQL container is not running")
                            time.sleep(5)
                            continue
                            
                        postgres.reload()  # Get latest state
                        postgres_health = postgres.attrs['State'].get('Health', {}).get('Status')
                        if postgres_health != "healthy":
                            self.logger.info(f"PostgreSQL container health: {postgres_health}")
                            time.sleep(5)
                            continue
                    except docker.errors.NotFound:
                        self.logger.info("PostgreSQL container not found")
                        return False
                    
                    # Check Keycloak container
                    try:
                        keycloak = client.containers.get("keycloak")
                        if keycloak.status != "running":
                            self.logger.info("Keycloak container is not running")
                            time.sleep(5)
                            continue
                            
                        keycloak.reload()  # Get latest state
                        keycloak_health = keycloak.attrs['State'].get('Health', {}).get('Status')
                        if keycloak_health != "healthy":
                            self.logger.info(f"Keycloak container health: {keycloak_health}")
                            time.sleep(5)
                            continue
                    except docker.errors.NotFound:
                        self.logger.info("Keycloak container not found")
                        return False
                    
                    # Check Keycloak API availability
                    http_port = env_vars.get('KEYCLOAK_HTTP_PORT', '8080')
                    try:
                        response = requests.get(f"http://localhost:{http_port}/auth/health/ready")
                        if response.status_code == 200:
                            self.logger.info("Keycloak API is responding")
                            return True
                    except RequestException:
                        self.logger.info("Keycloak API not yet responding")
                        time.sleep(5)
                        continue
                        
                except docker.errors.APIError as e:
                    self.logger.error(f"Docker API error: {e}")
                    return False
                    
                except Exception as e:
                    self.logger.error(f"Error checking deployment status: {e}")
                    time.sleep(5)
                    
            self.logger.error(f"Deployment not ready after {timeout} seconds timeout")
            return False
                
        except ImportError:
            self.logger.error("Docker SDK for Python is not installed")
            return False
        except Exception as e:
            self.logger.error(f"Failed to check deployment status: {e}")
            return False
    
    def _deploy_containers(self, env_vars: Dict[str, str], container_configs: Dict) -> bool:
        """
        Deploy Keycloak and PostgreSQL containers
        
        Args:
            env_vars: Dictionary of environment variables
            container_configs: Dictionary of container configurations
            
        Returns:
            bool: True if deployment was successful, False otherwise
        """
        try:
            # Import docker here to ensure it's only used when needed
            import docker
            client = docker.from_env()
            
            # Pull required Docker images
            required_images = [
                container_configs["postgres"]["image"],
                container_configs["keycloak"]["image"]
            ]
            
            all_present, missing_images = check_docker_images(required_images)
            if not all_present:
                self.logger.info(f"Pulling missing Docker images: {missing_images}")
                if not pull_docker_images(missing_images):
                    self.logger.error("Failed to pull required Docker images")
                    return False
            
            # Create Docker network if it doesn't exist
            network_name = env_vars.get('DOCKER_NETWORK', 'keycloak-network')
            try:
                client.networks.get(network_name)
            except docker.errors.NotFound:
                self.logger.info(f"Creating {network_name}")
                client.networks.create(network_name)
            
            # Start PostgreSQL container
            self.logger.info("Starting PostgreSQL container...")
            try:
                postgres = client.containers.get("postgres")
                if postgres.status != "running":
                    postgres.start()
            except docker.errors.NotFound:
                postgres = client.containers.run(
                    container_configs["postgres"]["image"],
                    name=container_configs["postgres"]["name"],
                    hostname=container_configs["postgres"]["hostname"],
                    environment={
                        "POSTGRES_DB": env_vars.get('DB_NAME', 'keycloak'),
                        "POSTGRES_USER": env_vars.get('DB_USER', 'keycloak'),
                        "POSTGRES_PASSWORD": env_vars.get('DB_PASSWORD')
                    },
                    volumes=container_configs["postgres"]["volumes"],
                    healthcheck=container_configs["postgres"]["healthcheck"],
                    restart_policy=container_configs["postgres"]["restart_policy"],
                    mem_limit=container_configs["postgres"]["resources"]["mem_limit"],
                    mem_reservation=container_configs["postgres"]["resources"]["mem_reservation"],
                    cpu_shares=container_configs["postgres"]["resources"]["cpu_shares"],
                    detach=True,
                    network=network_name
                )
            
            # Wait for PostgreSQL to be healthy
            self.logger.info("Waiting for PostgreSQL to be healthy...")
            postgres.reload()  # Get latest state
            postgres_health = None
            
            # Wait up to 60 seconds for PostgreSQL to become healthy
            start_time = time.time()
            while time.time() - start_time < 60:
                postgres.reload()
                postgres_health = postgres.attrs['State'].get('Health', {}).get('Status')
                if postgres_health == "healthy":
                    break
                time.sleep(2)
            
            if postgres_health != "healthy":
                self.logger.error("PostgreSQL failed to become healthy")
                return False
            
            # Prepare Keycloak environment variables
            keycloak_env = self._prepare_keycloak_environment(env_vars)
            
            # Start Keycloak container
            self.logger.info("Starting Keycloak container...")
            try:
                keycloak = client.containers.get("keycloak")
                if keycloak.status != "running":
                    keycloak.start()
            except docker.errors.NotFound:
                # Use optimized start command for better performance
                start_cmd = ["start", "--optimized"] if not env_vars.get('KEYCLOAK_DEV_MODE', False) else ["start-dev"]
                
                keycloak = client.containers.run(
                    container_configs["keycloak"]["image"],
                    command=start_cmd,
                    name=container_configs["keycloak"]["name"],
                    hostname=container_configs["keycloak"]["hostname"],
                    environment=keycloak_env,
                    volumes=container_configs["keycloak"]["volumes"],
                    healthcheck=container_configs["keycloak"]["healthcheck"],
                    restart_policy=container_configs["keycloak"]["restart_policy"],
                    mem_limit=container_configs["keycloak"]["resources"]["mem_limit"],
                    mem_reservation=container_configs["keycloak"]["resources"]["mem_reservation"],
                    cpu_shares=container_configs["keycloak"]["resources"]["cpu_shares"],
                    ports={
                        f'8080/tcp': int(env_vars.get('KEYCLOAK_HTTP_PORT', '8080')),
                        f'8443/tcp': int(env_vars.get('KEYCLOAK_HTTPS_PORT', '8443'))
                    },
                    detach=True,
                    network=network_name
                )
            
            # Wait for Keycloak to be ready
            self.logger.info("Waiting for Keycloak to become ready...")
            if not self.check_deployment_ready(env_vars, timeout=300):
                self.logger.error("Keycloak deployment failed to become ready")
                return False
            
            self.logger.info("Keycloak deployed successfully!")
            return True
            
        except docker.errors.APIError as e:
            self.logger.error(f"Docker API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to deploy containers: {e}")
            return False
    
    def _deploy_keycloak_config(self, env_vars: Dict[str, str]) -> bool:
        """
        Apply configuration to Keycloak using the ConfigLoader
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            # Import docker here to ensure it's only used when needed
            import docker
            client = docker.from_env()
            
            # Get Keycloak container
            try:
                keycloak = client.containers.get("keycloak")
            except docker.errors.NotFound:
                self.logger.error("Keycloak container not found")
                return False
                
            # Wait for Keycloak to be ready for configuration
            self.logger.info("Waiting for Keycloak to be ready for configuration...")
            time.sleep(10)  # Allow some additional time for internal services to stabilize
            
            # Get admin credentials
            admin_user = env_vars.get('KEYCLOAK_ADMIN', 'admin')
            admin_password = env_vars.get('KEYCLOAK_ADMIN_PASSWORD')
            
            # Create configuration loader
            config_loader = ConfigLoader(keycloak, admin_user, admin_password)
            
            # Prepare variables for templates
            realm_name = env_vars.get('KEYCLOAK_REALM_NAME', 'master')
            
            # Create variables dictionary for template substitution
            template_vars = {
                # Realm configuration
                'REALM_ID': env_vars.get('KEYCLOAK_REALM_ID', realm_name),
                'REALM_NAME': realm_name,
                'REALM_DISPLAY_NAME': env_vars.get('KEYCLOAK_REALM_DISPLAY_NAME', realm_name),
                
                # SMTP configuration
                'SMTP_HOST': env_vars.get('SMTP_HOST', ''),
                'SMTP_PORT': env_vars.get('SMTP_PORT', '25'),
                'SMTP_FROM': env_vars.get('SMTP_FROM', ''),
                'SMTP_FROM_DISPLAY_NAME': env_vars.get('SMTP_FROM_DISPLAY_NAME', 'Keycloak'),
                'SMTP_REPLY_TO': env_vars.get('SMTP_REPLY_TO', ''),
                'SMTP_REPLY_TO_DISPLAY_NAME': env_vars.get('SMTP_REPLY_TO_DISPLAY_NAME', ''),
                'SMTP_SSL': env_vars.get('SMTP_SSL', 'false'),
                'SMTP_STARTTLS': env_vars.get('SMTP_STARTTLS', 'true'),
                'SMTP_AUTH': env_vars.get('SMTP_AUTH', 'true'),
                'SMTP_USER': env_vars.get('SMTP_USER', ''),
                'SMTP_PASSWORD': env_vars.get('SMTP_PASSWORD', ''),
                
                # Client configuration
                'CLIENT_ID': env_vars.get('CLIENT_ID', 'app-client'),
                'CLIENT_NAME': env_vars.get('CLIENT_NAME', 'Application Client'),
                'CLIENT_DESCRIPTION': env_vars.get('CLIENT_DESCRIPTION', 'Client for main application'),
                'CLIENT_ROOT_URL': env_vars.get('CLIENT_ROOT_URL', 'https://app.example.com'),
                'CLIENT_REDIRECT_URI': env_vars.get('CLIENT_REDIRECT_URI', 'https://app.example.com/*'),
                'CLIENT_WEB_ORIGIN': env_vars.get('CLIENT_WEB_ORIGIN', 'https://app.example.com'),
                'CLIENT_SECRET': env_vars.get('CLIENT_SECRET', ''),
                
                # SPA Client configuration
                'SPA_CLIENT_ID': env_vars.get('SPA_CLIENT_ID', 'spa-client'),
                'SPA_CLIENT_NAME': env_vars.get('SPA_CLIENT_NAME', 'SPA Client'),
                'SPA_CLIENT_DESCRIPTION': env_vars.get('SPA_CLIENT_DESCRIPTION', 'Client for SPA'),
                'SPA_CLIENT_ROOT_URL': env_vars.get('SPA_CLIENT_ROOT_URL', 'https://spa.example.com'),
                'SPA_CLIENT_REDIRECT_URI': env_vars.get('SPA_CLIENT_REDIRECT_URI', 'https://spa.example.com/*'),
                'SPA_CLIENT_WEB_ORIGIN': env_vars.get('SPA_CLIENT_WEB_ORIGIN', 'https://spa.example.com')
            }
            
            # Apply configurations
            if not config_loader.apply_all_configs(realm_name, template_vars):
                self.logger.warning("Some Keycloak configurations could not be applied")
                return False
            
            self.logger.info(f"Keycloak configurations successfully applied to realm {realm_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply Keycloak configuration: {e}")
            return False
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute the main deployment operation"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Prepare container configurations
            container_configs = self._prepare_container_configs(env_vars)
            
            # Deploy Keycloak and PostgreSQL containers
            if not self._deploy_containers(env_vars, container_configs):
                self.logger.error("Failed to deploy containers")
                return False
            
            # Apply Keycloak configuration if not in dev mode
            if not env_vars.get('KEYCLOAK_DEV_MODE', False):
                if not self._deploy_keycloak_config(env_vars):
                    self.logger.warning("Failed to apply Keycloak configuration")
                    # This is a non-critical failure, so we'll continue
            
            self.logger.info("Keycloak deployment completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        try:
            # Import docker here to ensure it's only used when needed
            import docker
            client = docker.from_env()
            
            # Stop and remove Keycloak container if it exists
            try:
                keycloak = client.containers.get("keycloak")
                self.logger.info("Stopping Keycloak container...")
                keycloak.stop(timeout=10)
                self.logger.info("Removing Keycloak container...")
                keycloak.remove()
            except docker.errors.NotFound:
                pass
                
            # Stop and remove PostgreSQL container if it exists
            try:
                postgres = client.containers.get("postgres")
                self.logger.info("Stopping PostgreSQL container...")
                postgres.stop(timeout=10)
                self.logger.info("Removing PostgreSQL container...")
                postgres.remove()
            except docker.errors.NotFound:
                pass
                
            self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")
