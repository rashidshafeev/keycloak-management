import os
import subprocess
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger("step.keycloak_deployment.dependencies")

def check_keycloak_deployment_dependencies() -> bool:
    """
    Check if dependencies for the Keycloak server deployment and configuration step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    """
    try:
        # Check Docker installation
        docker_result = subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True
        )
        
        if docker_result.returncode != 0:
            logger.info("Docker is not installed")
            return False
        
        # Check Docker Compose installation
        compose_result = subprocess.run(
            ["docker", "compose", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True
        )
        
        if compose_result.returncode != 0:
            # Try older docker-compose command
            compose_result = subprocess.run(
                ["docker-compose", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True
            )
            
            if compose_result.returncode != 0:
                logger.info("Docker Compose is not installed")
                return False
        
        # Check if Docker daemon is running
        docker_info = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True
        )
        
        if docker_info.returncode != 0:
            logger.info("Docker daemon is not running")
            return False
        
        # Check if Docker network exists
        network_result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=keycloak-network", "--format", "{{.Name}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True
        )
        
        if not network_result.stdout.strip():
            logger.info("Docker keycloak-network does not exist")
            # This is not a critical failure, we'll create it later
        
        # Check if Python Docker SDK is installed
        try:
            import docker
            return True
        except ImportError:
            logger.info("Python Docker SDK is not installed")
            return False
            
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def install_keycloak_deployment_dependencies() -> bool:
    """
    Install dependencies for the Keycloak server deployment and configuration step
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Check if pip is available
        pip_result = subprocess.run(
            ["pip", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        
        if pip_result.returncode != 0:
            logger.error("pip is not installed, cannot proceed with dependency installation")
            return False
        
        # Install Python Docker SDK
        subprocess.run(
            ["pip", "install", "docker", "requests"],
            check=True
        )
        
        # Create Docker network if it doesn't exist
        network_result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=keycloak-network", "--format", "{{.Name}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True
        )
        
        if not network_result.stdout.strip():
            logger.info("Creating Docker keycloak-network")
            subprocess.run(
                ["docker", "network", "create", "keycloak-network"],
                check=True
            )
        
        # Verify installation
        return check_keycloak_deployment_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False

def check_docker_images(images: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if required Docker images are available locally
    
    Args:
        images: List of image names to check
        
    Returns:
        Tuple[bool, List[str]]: (All images available, List of missing images)
    """
    missing_images = []
    
    for image in images:
        result = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        
        if result.returncode != 0:
            missing_images.append(image)
    
    return len(missing_images) == 0, missing_images

def pull_docker_images(images: List[str]) -> bool:
    """
    Pull required Docker images
    
    Args:
        images: List of image names to pull
        
    Returns:
        bool: True if all images were pulled successfully
    """
    try:
        for image in images:
            logger.info(f"Pulling Docker image: {image}")
            subprocess.run(
                ["docker", "pull", image],
                check=True
            )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to pull Docker image: {e.cmd}")
        return False
