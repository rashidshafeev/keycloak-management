# Migration Guide: Centralized to Modular Architecture

This guide provides instructions for migrating from the centralized dependency management architecture to the new modular step-based architecture.

## Overview of Changes

The major changes in the new architecture are:

1. **Directory Structure**: Steps are now organized in a dedicated `steps` directory with subdirectories for each category.
2. **Dependency Management**: Each step now manages its own dependencies rather than relying on a central dependency manager.
3. **Environment Variables**: Each step defines and manages its own required environment variables.
4. **Orchestration**: The orchestrator is simplified and focused solely on step execution sequence.
5. **CLI Interface**: CLI commands are more explicit about which steps they execute.

## Migration Process

### 1. Project Structure Migration

**Old structure:**
```
src/
├── deployment/
│   ├── base.py
│   └── orchestrator.py
├── keycloak/
│   └── deploy.py
├── monitoring/
│   └── prometheus.py
├── security/
│   └── ssl.py
└── system/
    └── prepare.py
```

**New structure:**
```
src/
├── core/
│   ├── base.py
│   └── orchestrator.py
└── steps/
    ├── system/
    │   └── prepare.py
    ├── docker/
    │   └── setup.py
    ├── keycloak/
    │   └── deploy.py
    ├── certificates/
    │   └── ssl.py
    └── monitoring/
        └── prometheus.py
```

#### Migration steps:

1. Create the new directory structure
2. Move existing step implementations to the corresponding directory under `src/steps/`
3. Create `__init__.py` files for each step package

### 2. Base Class Migration

**From:**
```python
# src/deployment/base.py
class DeploymentStep:
    def __init__(self, name, can_cleanup=False):
        self.name = name
        self.can_cleanup = can_cleanup
        self.logger = logging.getLogger(name)
```

**To:**
```python
# src/core/base.py
class BaseStep(ABC):
    def __init__(self, name: str, can_cleanup: bool = False):
        self.name = name
        self.can_cleanup = can_cleanup
        self.logger = logging.getLogger(f"step.{name}")
        self.required_vars = []
    
    @abstractmethod
    def _check_dependencies(self) -> bool:
        pass
    
    @abstractmethod
    def _install_dependencies(self) -> bool:
        pass
    
    @abstractmethod
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        pass
```

### 3. Step Implementation Migration

For each existing step, modify the implementation to follow the new pattern:

**From:**
```python
class SystemPreparationStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("system_preparation", can_cleanup=False)
        self.config = config
    
    def execute(self) -> bool:
        # Implementation
```

**To:**
```python
class SystemPreparationStep(BaseStep):
    def __init__(self):
        super().__init__("system_preparation", can_cleanup=False)
        self.required_vars = [
            {
                'name': 'INSTALL_ROOT',
                'prompt': 'Enter installation root directory',
                'default': '/opt/keycloak'
            },
            # More variables
        ]
    
    def _check_dependencies(self) -> bool:
        # Dependency checking implementation
    
    def _install_dependencies(self) -> bool:
        # Dependency installation implementation
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        # Deployment implementation
```

### 4. Dependency Management Migration

**From:** Using the centralized dependency manager:
```python
from ..utils.dependencies import DependencyManager

dependency_manager = DependencyManager()
if not dependency_manager.check_docker()[0]:
    dependency_manager.install_docker()
```

**To:** Each step handling its own dependencies:
```python
def _check_dependencies(self) -> bool:
    try:
        # Check if docker command exists
        docker_version = self._run_command(["docker", "--version"], check=True)
        return True
    except:
        return False

def _install_dependencies(self) -> bool:
    try:
        # Install Docker
        self._run_command(['apt-get', 'update'])
        self._run_command(['apt-get', 'install', '-y', 'docker.io'])
        return True
    except:
        return False
```

### 5. Environment Variable Migration

**From:** Using the central configuration:
```python
def execute(self) -> bool:
    domain = self.config.get('KEYCLOAK_DOMAIN', 'localhost')
    port = self.config.get('KEYCLOAK_PORT', '8443')
    # Implementation using config
```

**To:** Each step managing its own variables:
```python
def __init__(self):
    super().__init__("keycloak_deployment", can_cleanup=True)
    self.required_vars = [
        {
            'name': 'KEYCLOAK_DOMAIN',
            'prompt': 'Enter Keycloak domain name',
            'default': 'localhost'
        },
        {
            'name': 'KEYCLOAK_PORT',
            'prompt': 'Enter Keycloak port',
            'default': '8443'
        }
    ]

def _deploy(self, env_vars: Dict[str, str]) -> bool:
    domain = env_vars.get('KEYCLOAK_DOMAIN', 'localhost')
    port = env_vars.get('KEYCLOAK_PORT', '8443')
    # Implementation using env_vars
```

### 6. Orchestrator Migration

**From:** Using the complex orchestrator with many responsibilities:
```python
class DeploymentOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.steps = []
        # Various other properties and setup
    
    def deploy(self) -> bool:
        # Complex deployment logic with many responsibilities
        # Environment setup, dependency checking, etc.
```

**To:** Using the simplified orchestrator:
```python
class StepOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.steps = []
    
    def add_step(self, step: BaseStep) -> None:
        self.steps.append(step)
    
    def execute(self) -> bool:
        # Simple execution of steps in sequence
```

### 7. CLI Command Migration

**From:** Using centralized commands:
```python
@cli.command()
def deploy():
    # Load config
    # Create orchestrator
    # Add steps implicitly
    orchestrator.deploy()
```

**To:** Explicitly specifying the steps:
```python
@cli.command()
def deploy():
    # Load environment
    env_vars = load_environment()
    
    # Create orchestrator
    orchestrator = StepOrchestrator(env_vars)
    
    # Import and add steps explicitly
    from src.steps.system import SystemPreparationStep
    from src.steps.docker import DockerSetupStep
    from src.steps.keycloak import KeycloakDeployStep
    
    # Add steps in execution order
    orchestrator.add_step(SystemPreparationStep())
    orchestrator.add_step(DockerSetupStep())
    orchestrator.add_step(KeycloakDeployStep())
    
    # Execute deployment
    orchestrator.execute()
```

## Testing Your Migration

Test each component as you migrate:

1. Start with the core classes: `BaseStep` and `StepOrchestrator`
2. Migrate one step at a time, testing each in isolation
3. Test the complete flow with a simple step sequence
4. Gradually add more complex steps and test again

## Benefits After Migration

After completing the migration, you'll enjoy:

1. **Greater modularity**: Adding new deployment steps is easier
2. **Better maintainability**: Changes to one step don't affect others
3. **Enhanced testability**: Steps can be tested in isolation
4. **Improved extensibility**: Customize and arrange steps to fit your needs
5. **Better separation of concerns**: Each step has a clear single responsibility

## Common Issues and Solutions

### Issue: Step fails with missing dependency

**Solution:** Ensure the step properly implements `_check_dependencies()` and `_install_dependencies()`. Consider dependencies between steps - some steps may require others to run first.

### Issue: Environment variables not available

**Solution:** Check that each step correctly defines its `required_vars` list and that the environment file is properly loaded.

### Issue: Steps execute out of order

**Solution:** Ensure steps are added to the orchestrator in the correct sequence in the CLI command.

### Issue: Cannot find module errors

**Solution:** Update import paths to reflect the new directory structure and ensure `__init__.py` files are properly created.