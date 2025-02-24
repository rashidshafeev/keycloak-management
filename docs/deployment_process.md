# Deployment Process Documentation

## Overview
This document describes the improved deployment process with a focus on environment variables and dependency management.

## Environment Variables Management

Each deployment step uses the `EnvironmentManager` to handle its required variables:

```python
from src.utils.environment import get_environment_manager

class KeycloakDeploymentStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("keycloak_deployment", can_cleanup=True)
        
        # Get environment manager
        env_manager = get_environment_manager()
        
        # Define required variables
        required_vars = [
            {
                'name': 'KEYCLOAK_PORT',
                'prompt': 'Enter Keycloak port',
                'default': '8443'
            },
            {
                'name': 'KEYCLOAK_ADMIN_EMAIL',
                'prompt': 'Enter admin email',
                'default': 'admin@localhost'
            }
        ]
        
        # Get variables (will prompt if missing)
        self.env_vars = env_manager.get_or_prompt_vars(required_vars)
```

### Benefits
- Variables are requested only when needed
- Values are cached in .env file
- Secure storage (600 permissions)
- Default values support
- Clear user prompts

## Dependencies Management

Each step handles its own dependencies directly in the code:

```python
def _check_dependencies(self) -> bool:
    """Check if required dependencies are installed"""
    try:
        # Docker check
        subprocess.run(['docker', '--version'], check=True)
        subprocess.run(['docker-compose', '--version'], check=True)
        
        # Database client check
        subprocess.run(['psql', '--version'], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        self.logger.error(f"Missing required dependency: {e}")
        return False
    except Exception as e:
        self.logger.error(f"Dependency check failed: {e}")
        return False

def _install_dependencies(self) -> bool:
    """Install missing dependencies"""
    try:
        # Install Docker if needed
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'docker.io'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'docker-compose'], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        self.logger.error(f"Failed to install dependencies: {e}")
        return False
```

### Benefits
- Dependencies checked when needed
- Clear error reporting
- Step-specific requirements
- No unnecessary installations
- Simple rollback capability

## Deployment Step Pattern

Each deployment step follows this pattern:

```python
def execute(self) -> bool:
    """Execute the deployment step"""
    try:
        # 1. Check dependencies
        if not self._check_dependencies():
            if not self._install_dependencies():
                self.logger.error("Failed to install required dependencies")
                return False
        
        # 2. Get environment variables
        try:
            env_vars = get_environment_manager().get_or_prompt_vars(self.required_vars)
        except Exception as e:
            self.logger.error(f"Failed to get environment variables: {e}")
            return False
        
        # 3. Execute main operation
        try:
            if not self._deploy(env_vars):
                raise Exception("Deployment failed")
            
            self.logger.info(f"{self.name} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            self._cleanup()
            return False
            
    except Exception as e:
        self.logger.error(f"Step execution failed: {e}")
        return False
```

### Key Features
1. **Dependency Management**
   - Check dependencies first
   - Install only if needed
   - Clear error reporting

2. **Environment Variables**
   - Get required variables
   - Use cached values when available
   - Prompt only when needed

3. **Error Handling**
   - Comprehensive error catching
   - Proper cleanup on failure
   - Detailed logging

4. **Status Reporting**
   - Clear success/failure indication
   - Detailed error messages
   - Operation logging

## Example: Keycloak Deployment

The Keycloak deployment step would implement this pattern:

```python
class KeycloakDeploymentStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("keycloak_deployment", can_cleanup=True)
        self.config = config
        self.required_vars = [
            {
                'name': 'KEYCLOAK_PORT',
                'prompt': 'Enter Keycloak port',
                'default': '8443'
            },
            {
                'name': 'KEYCLOAK_ADMIN_EMAIL',
                'prompt': 'Enter admin email',
                'default': 'admin@localhost'
            }
        ]
    
    def _check_dependencies(self) -> bool:
        # Check Docker and database dependencies
        ...
    
    def _deploy(self, env_vars: dict) -> bool:
        # Deploy Keycloak using environment variables
        ...
    
    def _cleanup(self) -> None:
        # Clean up on failure
        ...
```

## Best Practices

1. **Environment Variables**
   - Request only what's needed
   - Provide clear prompts
   - Use meaningful defaults
   - Validate inputs
   - Secure sensitive data

2. **Dependencies**
   - Check before using
   - Install only if needed
   - Verify installations
   - Handle failures gracefully
   - Clean up on failure

3. **Error Handling**
   - Catch specific exceptions
   - Provide clear error messages
   - Log all operations
   - Clean up on failure
   - Report detailed status

4. **Code Organization**
   - Keep methods focused
   - Clear responsibility separation
   - Consistent pattern usage
   - Proper documentation
   - Comprehensive logging
