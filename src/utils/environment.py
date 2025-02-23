import os
import sys
import subprocess
import click
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
import venv
from .system_checks import check_docker

class EnvironmentSetup:
    def __init__(self):
        self.install_dir = Path("/opt/fawz/keycloak")
        self.venv_dir = self.install_dir / "venv"
        self.config_dir = Path("/etc/keycloak")
        self.log_dir = Path("/var/log/keycloak")
        self.backup_dir = Path("/var/backup/keycloak")

    def setup_directories(self):
        """Create necessary directories with proper permissions"""
        directories = [
            self.install_dir,
            self.config_dir,
            self.log_dir,
            self.backup_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Set proper permissions (owner read/write/execute, group read/execute)
            os.chmod(directory, 0o750)

    def install_system_dependencies(self) -> bool:
        """Install required system packages"""
        try:
            if sys.platform.startswith('linux'):
                # Detect package manager
                if shutil.which('apt-get'):
                    subprocess.run([
                        'apt-get', 'update'
                    ], check=True)
                    subprocess.run([
                        'apt-get', 'install', '-y',
                        'python3-venv',
                        'python3-pip',
                        'python3-dev',
                        'build-essential',
                        'libssl-dev',
                        'libffi-dev',
                        'git',
                        'curl',
                        'wget',
                        'ufw'
                    ], check=True)
                elif shutil.which('apk'):
                    subprocess.run([
                        'apk', 'add', '--no-cache',
                        'python3',
                        'py3-pip',
                        'python3-dev',
                        'gcc',
                        'musl-dev',
                        'openssl-dev',
                        'libffi-dev',
                        'git',
                        'curl',
                        'wget'
                    ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to install system dependencies: {e}", err=True)
            return False

    def setup_docker(self) -> bool:
        """Install and configure Docker if not present"""
        docker_ok, _ = check_docker()
        if docker_ok:
            return True

        try:
            if sys.platform.startswith('linux'):
                # Install Docker using official method
                subprocess.run([
                    'curl', '-fsSL', 'https://get.docker.com', '-o', 'get-docker.sh'
                ], check=True)
                subprocess.run(['sh', 'get-docker.sh'], check=True)
                
                # Start and enable Docker service
                subprocess.run(['systemctl', 'start', 'docker'], check=True)
                subprocess.run(['systemctl', 'enable', 'docker'], check=True)
                
                # Configure Docker network
                subprocess.run([
                    'docker', 'network', 'create', 'keycloak-network'
                ], check=True)
                
                return True
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to setup Docker: {e}", err=True)
            return False

    def setup_firewall(self) -> bool:
        """Configure firewall rules"""
        try:
            if sys.platform.startswith('linux') and shutil.which('ufw'):
                # Allow necessary ports
                ports = ['80/tcp', '443/tcp', '8080/tcp', '8443/tcp']
                for port in ports:
                    subprocess.run(['ufw', 'allow', port], check=True)
                
                # Configure Docker rules
                docker_rules = """
[Docker]
title=Docker
description=Docker container engine
ports=2375,2376,2377,7946/tcp|7946/udp|4789/udp
"""
                docker_rules_file = Path('/etc/ufw/applications.d/docker')
                docker_rules_file.write_text(docker_rules)
                
                subprocess.run(['ufw', 'reload'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to configure firewall: {e}", err=True)
            return False

    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment"""
        try:
            if not self.venv_dir.exists():
                venv.create(self.venv_dir, with_pip=True)
            
            # Activate virtual environment and install requirements
            pip_path = self.venv_dir / 'bin' / 'pip'
            subprocess.run([
                str(pip_path), 'install', '-r', 'requirements.txt'
            ], check=True)
            
            return True
        except Exception as e:
            click.echo(f"Failed to setup Python environment: {e}", err=True)
            return False

    def prompt_for_config(self) -> Dict[str, Any]:
        """Prompt user for configuration values"""
        config = {}
        
        # Basic configuration
        config['domain'] = click.prompt("Enter domain name for Keycloak", type=str)
        config['admin_email'] = click.prompt("Enter admin email", type=str)
        
        # Security configuration
        config['admin_password'] = click.prompt(
            "Enter admin password",
            type=str,
            hide_input=True,
            confirmation_prompt=True
        )
        
        # Database configuration
        config['db_vendor'] = click.prompt(
            "Enter database vendor",
            type=click.Choice(['postgres', 'mysql']),
            default='postgres'
        )
        config['db_host'] = click.prompt("Enter database host", default="localhost")
        config['db_port'] = click.prompt("Enter database port", type=int, default=5432)
        config['db_name'] = click.prompt("Enter database name", default="keycloak")
        config['db_user'] = click.prompt("Enter database user", default="keycloak")
        config['db_password'] = click.prompt(
            "Enter database password",
            type=str,
            hide_input=True,
            confirmation_prompt=True
        )
        
        # SSL configuration
        config['ssl_enabled'] = click.confirm("Enable SSL?", default=True)
        if config['ssl_enabled']:
            config['ssl_provider'] = click.prompt(
                "SSL provider",
                type=click.Choice(['letsencrypt', 'custom']),
                default='letsencrypt'
            )
            if config['ssl_provider'] == 'custom':
                config['ssl_cert_path'] = click.prompt("Enter path to SSL certificate")
                config['ssl_key_path'] = click.prompt("Enter path to SSL private key")
        
        # Monitoring configuration
        config['monitoring_enabled'] = click.confirm("Enable monitoring?", default=True)
        if config['monitoring_enabled']:
            config['prometheus_retention_days'] = click.prompt(
                "Enter Prometheus retention days",
                type=int,
                default=15
            )
        
        return config

    def save_environment(self, config: Dict[str, Any]):
        """Save configuration to .env file"""
        env_content = [
            "# Keycloak Configuration",
            f"KEYCLOAK_DOMAIN={config['domain']}",
            f"KEYCLOAK_ADMIN_EMAIL={config['admin_email']}",
            f"KEYCLOAK_ADMIN_PASSWORD={config['admin_password']}",
            "",
            "# Database Configuration",
            f"DB_VENDOR={config['db_vendor']}",
            f"DB_HOST={config['db_host']}",
            f"DB_PORT={config['db_port']}",
            f"DB_NAME={config['db_name']}",
            f"DB_USER={config['db_user']}",
            f"DB_PASSWORD={config['db_password']}",
            "",
            "# SSL Configuration",
            f"SSL_ENABLED={str(config['ssl_enabled']).lower()}"
        ]
        
        if config['ssl_enabled']:
            env_content.extend([
                f"SSL_PROVIDER={config['ssl_provider']}",
                f"SSL_CERT_PATH={config.get('ssl_cert_path', '')}",
                f"SSL_KEY_PATH={config.get('ssl_key_path', '')}"
            ])
        
        if config.get('monitoring_enabled'):
            env_content.extend([
                "",
                "# Monitoring Configuration",
                f"PROMETHEUS_RETENTION_DAYS={config['prometheus_retention_days']}"
            ])
        
        # Write to .env file
        env_file = Path('.env')
        env_file.write_text('\n'.join(env_content))

    def setup(self) -> bool:
        """Run complete environment setup"""
        try:
            click.echo("Setting up Keycloak environment...")
            
            # Create necessary directories
            self.setup_directories()
            
            # Install system dependencies
            if not self.install_system_dependencies():
                return False
            
            # Setup Docker
            if not self.setup_docker():
                return False
            
            # Configure firewall
            if not self.setup_firewall():
                return False
            
            # Setup Python environment
            if not self.setup_python_environment():
                return False
            
            # Get configuration from user
            config = self.prompt_for_config()
            
            # Save configuration
            self.save_environment(config)
            
            click.echo("Environment setup completed successfully!")
            return True
            
        except Exception as e:
            click.echo(f"Environment setup failed: {e}", err=True)
            return False

def setup_environment() -> Dict[str, Any]:
    """Main entry point for environment setup"""
    env_setup = EnvironmentSetup()
    if not env_setup.setup():
        raise click.ClickException("Failed to setup environment")
    return load_environment()

def load_environment() -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if not env_file.exists():
        raise click.ClickException(".env file not found. Run setup first.")
    
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars
