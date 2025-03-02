import os
from pathlib import Path
from typing import Dict, Any
import yaml
import json
import jsonschema
from jsonschema import validate, ValidationError
import click

class YamlConfigLoader:
    """Loads and validates YAML configuration files"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.schema_dir = config_dir / "schemas"
        
        # Create schema directory if it doesn't exist
        if not self.schema_dir.exists():
            self.schema_dir.mkdir(parents=True)
    
    def _replace_env_vars(self, value: Any) -> Any:
        """Replace environment variables in string values"""
        if isinstance(value, str):
            # Replace ${VAR} with environment variable
            if value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.environ.get(env_var, value)
            return value
        elif isinstance(value, dict):
            return {k: self._replace_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._replace_env_vars(v) for v in value]
        return value
    
    def load_config(self, component: str) -> Dict[str, Any]:
        """Load YAML configuration file for a component"""
        config_file = self.config_dir / f"{component}.yml"
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            try:
                config = yaml.safe_load(f)
                return self._replace_env_vars(config)
            except yaml.YAMLError as e:
                raise click.ClickException(f"Error parsing {component}.yml: {str(e)}")
    
    def validate_schema(self, config: Dict[str, Any], schema_file: str) -> None:
        """Validate configuration against JSON schema"""
        schema_path = self.schema_dir / schema_file
        if not schema_path.exists():
            click.echo(f"Warning: Schema file not found: {schema_file}")
            return
            
        with open(schema_path, 'r') as f:
            try:
                schema = json.load(f)
                validate(instance=config, schema=schema)
            except json.JSONDecodeError as e:
                raise click.ClickException(f"Error parsing schema {schema_file}: {str(e)}")
            except ValidationError as e:
                raise click.ClickException(f"Configuration validation failed: {str(e)}")
    
    def create_schema_template(self, component: str, schema: Dict[str, Any]) -> None:
        """Create a JSON schema file for a component"""
        schema_file = self.schema_dir / f"{component}_schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
            click.echo(f"Created schema file: {schema_file}")
