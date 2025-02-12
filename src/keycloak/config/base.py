# /keycloak-management/src/keycloak/config/base.py
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
import click
from .yaml_loader import YamlConfigLoader
import json
import os

class ConfigurationError(Exception):
    """Base class for configuration errors"""
    pass

class ValidationError(ConfigurationError):
    """Raised when configuration validation fails"""
    pass

class RollbackError(ConfigurationError):
    """Raised when configuration rollback fails"""
    pass

class KeycloakConfigStep(ABC):
    """Base class for Keycloak configuration steps"""
    
    def __init__(self, name: str, config_dir: Path):
        self.name = name
        self.config_dir = config_dir
        self.logger = logging.getLogger(f"keycloak_config.{name}")
        self.changes: List[Dict[str, Any]] = []
        self.yaml_loader = YamlConfigLoader(config_dir)
        self._setup_logging()
        
        # Schema validation
        self.schema_file: Optional[str] = None
        self.required_fields: Set[str] = set()
        self.optional_fields: Set[str] = set()
        
        # Dependencies
        self.dependencies: List[str] = []

    def _setup_logging(self):
        """Setup logging for this configuration step"""
        log_dir = Path("logs/keycloak")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / f"{self.name}.log")
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)

    def validate(self, config: dict) -> bool:
        """Validate configuration before applying"""
        try:
            # Validate against JSON schema if available
            if self.schema_file:
                self.yaml_loader.validate_schema(config, self.schema_file)
            
            # Check required fields
            config_section = config.get(self.name, {})
            missing_fields = self.required_fields - set(config_section.keys())
            if missing_fields:
                raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Call implementation-specific validation
            return self._validate_impl(config)
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            raise ValidationError(str(e))

    def execute(self, config: dict) -> bool:
        """Execute configuration step"""
        try:
            # Record initial state for rollback
            self._record_initial_state()
            
            # Execute implementation
            success = self._execute_impl(config)
            
            if success:
                self.logger.info(f"Successfully applied {self.name} configuration")
            else:
                self.logger.error(f"Failed to apply {self.name} configuration")
                self.rollback()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}")
            self.rollback()
            raise ConfigurationError(str(e))

    def rollback(self) -> bool:
        """Rollback changes made by this step"""
        try:
            if not self.changes:
                return True
                
            success = self._rollback_impl()
            
            if success:
                self.logger.info("Successfully rolled back changes")
                self.changes.clear()
            else:
                self.logger.error("Failed to rollback changes")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            raise RollbackError(str(e))

    def _record_initial_state(self):
        """Record the initial state for rollback"""
        pass

    @abstractmethod
    def _validate_impl(self, config: dict) -> bool:
        """Implementation-specific validation"""
        pass

    @abstractmethod
    def _execute_impl(self, config: dict) -> bool:
        """Implementation-specific execution"""
        pass

    @abstractmethod
    def _rollback_impl(self) -> bool:
        """Implementation-specific rollback"""
        pass

    def run_kcadm_command(self, command: str, *args: str) -> subprocess.CompletedProcess:
        """Run a Keycloak admin CLI command"""
        cmd = ["kcadm.sh", command] + list(args)
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            self.logger.error(f"Command failed: {result.stderr}")
            raise ConfigurationError(f"kcadm command failed: {result.stderr}")
            
        return result

    def _run_kcadm(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run kcadm.sh command with proper error handling"""
        try:
            cmd = ["kcadm.sh"] + list(args)
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"Command stderr: {result.stderr}")
                
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e.stderr}")
            raise

    def _wait_for_keycloak(self, config: dict):
        """Wait for Keycloak to be ready"""
        max_retries = 30
        retry = 0
        
        self.logger.info("Waiting for Keycloak to be ready...")
        while retry < max_retries:
            try:
                subprocess.run(
                    ["curl", "-s", f"http://localhost:{config['port']}/health"],
                    check=True, capture_output=True
                )
                self.logger.info("Keycloak is ready")
                return
            except subprocess.CalledProcessError:
                retry += 1
                self.logger.debug(f"Attempt {retry}/{max_retries}")
                subprocess.run(["sleep", "5"])
        
        raise TimeoutError("Keycloak failed to start")

    def _record_change(self, action: str, details: dict):
        """Record a change for potential rollback"""
        self.changes.append({
            "action": action,
            "details": details,
            "timestamp": logging.Formatter.formatTime(logging.Formatter(), None)
        })
        self.logger.info(f"Recorded change: {action} - {details}")

    def _authenticate(self, config: dict):
        """Authenticate with Keycloak"""
        self._run_kcadm(
            "config", "credentials",
            "--server", f"http://localhost:{config['port']}",
            "--realm", "master",
            "--user", config["admin"]["username"],
            "--password", config["admin"]["password"]
        )

class BaseConfigurator:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.logger = logging.getLogger(f"keycloak_config.{self.__class__.__name__}")

    def _load_config_file(self, filename: str) -> dict:
        """Load configuration from file if exists"""
        config_file = self.config_dir / filename
        if config_file.exists():
            if filename.endswith('.json'):
                return json.loads(config_file.read_text())
            elif filename.endswith('.yaml') or filename.endswith('.yml'):
                return self.yaml_loader.load_config(config_file)
        return {}

    def _get_env_value(self, key: str, default: str = None) -> str:
        """Get value from environment variable"""
        return os.environ.get(key, default)

    def configure(self, interactive: bool = False):
        """Configure component"""
        raise NotImplementedError