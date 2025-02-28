import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.docker_setup.dependencies")

def check_docker_dependencies() -> bool:
    """
    Check if Docker is installed and running
    
    Returns:
        bool: True if Docker is installed and running, False otherwise
    """
    try:
        # Check if docker command exists
        docker_version = subprocess.run(
            ["docker", "--version"], 
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if docker_version.returncode != 0:
            logger.warning("Docker is not installed or not in PATH")
            return False
            
        logger.info(f"Docker version: {docker_version.stdout.strip()}")
        
        # Check if docker daemon is running
        docker_info = subprocess.run(
            ["docker", "info"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if docker_info.returncode != 0:
            logger.warning("Docker daemon is not running")
            return False
        
        # Check if docker-compose is available (either as plugin or standalone)
        try:
            compose_cmd = ["docker", "compose", "version"]
            compose_version = subprocess.run(
                compose_cmd, 
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if compose_version.returncode == 0:
                logger.info(f"Docker Compose (plugin) version: {compose_version.stdout.strip()}")
                return True
        except Exception:
            pass
        
        # Try with standalone compose
        try:
            compose_cmd = ["docker-compose", "--version"]
            compose_version = subprocess.run(
                compose_cmd, 
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if compose_version.returncode == 0:
                logger.info(f"Docker Compose (standalone) version: {compose_version.stdout.strip()}")
                return True
            else:
                logger.warning("Docker Compose is not available")
                return False
        except Exception:
            logger.warning("Docker Compose is not available")
            return False
            
    except FileNotFoundError:
        logger.warning("Docker command not found")
        return False
    except Exception as e:
        logger.error(f"Error checking Docker dependencies: {str(e)}")
        return False

def install_docker_dependencies() -> bool:
    """
    Install Docker and Docker Compose
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    # Skip if not on a Debian-based system
    if not os.path.exists('/etc/debian_version'):
        logger.error("Cannot install Docker on non-Debian system")
        return False
        
    try:
        # Update package lists
        subprocess.run(['apt-get', 'update'], check=True)
        
        # Install dependencies for Docker repository
        subprocess.run([
            'apt-get', 'install', '-y',
            'apt-transport-https',
            'ca-certificates',
            'curl',
            'gnupg',
            'lsb-release'
        ], check=True)
        
        # Add Docker's official GPG key
        keyring_dir = '/etc/apt/keyrings'
        os.makedirs(keyring_dir, exist_ok=True)
        
        subprocess.run([
            'curl', '-fsSL',
            'https://download.docker.com/linux/debian/gpg',
            '-o', '/etc/apt/keyrings/docker.asc'
        ], check=True)
        
        # Add the Docker repository
        os_codename = subprocess.run(
            ['lsb_release', '-cs'],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        ).stdout.strip()
        
        arch = subprocess.run(
            ['dpkg', '--print-architecture'],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        ).stdout.strip()
        
        with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
            f.write(
                f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] "
                f"https://download.docker.com/linux/debian "
                f"{os_codename} stable"
            )
        
        # Install Docker packages
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run([
            'apt-get', 'install', '-y',
            'docker-ce',
            'docker-ce-cli',
            'containerd.io',
            'docker-buildx-plugin',
            'docker-compose-plugin'
        ], check=True)
        
        # Start and enable the Docker service
        subprocess.run(['systemctl', 'enable', 'docker'], check=True)
        subprocess.run(['systemctl', 'start', 'docker'], check=True)
        
        # Verify installation
        return check_docker_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Docker: Command failed: {e.cmd}")
        return False
    except Exception as e:
        logger.error(f"Failed to install Docker: {str(e)}")
        return False