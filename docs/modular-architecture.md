# Modular Keycloak Management System

## Overview

This document describes the modular architecture of the Keycloak Management System, where each deployment step is fully independent and self-contained. This approach improves maintainability, testing, and extensibility of the deployment process.

## Key Principles

1. **Self-Contained Steps**: Each deployment step manages its own dependencies and environment variables.
2. **Decentralized Dependency Management**: Steps check and install their own dependencies.
3. **Independent Configuration**: Each step defines and validates its required environment variables.
4. **Clean Separation**: Steps are organized in a directory structure that reflects their purpose.
5. **Standardized Interface**: All steps follow a common base class contract.

## Directory Structure

```
keycloak-management/
├── install.sh                 # Main installation script
├── kcmanage.py                # CLI entry point
├── requirements.txt           # Global Python dependencies
├── README.md
├── config/                    # Configuration templates
│   └── templates/             # YAML templates for Keycloak config
├── docs/                      # Documentation
└── src/
    ├── core/                  # Core functionality
    │   ├── base.py            # Base classes
    │   ├── logging.py         # Logging setup
    │   └── orchestrator.py    # Simplified orchestrator
    ├── steps/                 # Each step in its own module
    │   ├── system/            # System preparation step
    │   │   ├── __init__.py
    │   │   ├── dependencies.py # Step-specific dependencies
    │   │   ├── environment.py  # Step-specific environment vars
    │   │   └── prepare.py      # Implementation
    │   ├── docker/            # Docker setup step
    │   │   ├── __init__.py
    │   │   ├── dependencies.py
    │   │   ├── environment.py
    │   │   └── setup.py
    │   ├── certificates/      # Certificate management step
    │   │   ├── __init__.py
    │   │   ├── dependencies.py
    │   │   ├── environment.py
    │   │   └── ssl.py
    │   └── ... (other steps with similar structure)
    └── utils/                 # Shared utilities
        ├── __init__.py
        ├── environment.py     # Environment variable management
        └── misc.py            # Miscellaneous helpers
```

## Step Module Structure

Each step is organized as a module with multiple files:

1. **Implementation File** (e.g., `prepare.py`): Contains the BaseStep implementation
2. **Dependencies File** (e.g., `dependencies.py`): Manages dependency checking and installation
3. **Environment File** (e.g., `environment.py`): Defines and validates environment variables 
4. **__init__.py**: Exports the step class for external use

This structure ensures each aspect of the step is cleanly separated and makes it easy to understand and modify each component independently.

## Base Step Class

All deployment steps inherit from the `BaseStep` abstract base class, which defines a consistent interface:

```python
class BaseStep(ABC):
    def __init__(self, name: str, can_cleanup: bool = False):
        # Initialize the step with name and cleanup capability
        
    def execute(self) -> bool:
        # Main execution method that orchestrates:
        # 1. Dependency checking and installation
        # 2. Environment variable acquisition
        # 3. Deployment operation
        # 4. Cleanup on failure if supported
        
    @abstractmethod
    def _check_dependencies(self) -> bool:
        # Check if required dependencies are installed
        
    @abstractmethod
    def _install_dependencies(self) -> bool:
        # Install required dependencies
        
    @abstractmethod
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        # Execute the main deployment operation
        
    def _cleanup(self) -> None:
        # Clean up after a failed deployment
```

## Step Lifecycle

Each step follows a standardized lifecycle:

1. **Initialization**: The step is instantiated with a name and cleanup capability flag.
2. **Dependency Check**: The step checks if its required dependencies are installed.
3. **Dependency Installation**: If dependencies are missing, the step attempts to install them.
4. **Environment Variables**: The step requests its required environment variables.
5. **Deployment**: The step performs its main deployment operation.
6. **Cleanup**: If deployment fails and cleanup is supported, the step performs cleanup.

## Dependencies Management

Each step defines its dependencies in a separate `dependencies.py` file that contains two key functions:

```python
def check_step_name_dependencies() -> bool:
    """Check if dependencies are installed"""
    # Implementation

def install_step_name_dependencies() -> bool:
    """Install required dependencies"""
    # Implementation
```

This approach allows each step to:
- Isolate dependency logic from core implementation
- Handle platform-specific dependency management
- Provide clear dependency documentation
- Implement custom verification logic

## Environment Variable Management

Each step defines its environment variables in a separate `environment.py` file with two key functions:

```python
def get_required_variables() -> List[Dict]:
    """Define required environment variables"""
    return [
        {
            'name': 'VARIABLE_NAME',
            'prompt': 'User-friendly prompt text',
            'default': 'default-value'
        }
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    """Validate environment variables"""
    # Validation logic
    return True
```

This pattern provides:
- Clear documentation of required variables
- Input validation specific to the step
- Default values appropriate for the step's needs
- Separation of concerns from deployment logic

## Orchestration

The `StepOrchestrator` class manages the execution of steps:

1. Steps are added to the orchestrator in the desired execution order.
2. The orchestrator executes each step sequentially.
3. If any step fails, the orchestration is stopped and an error is reported.
4. After successful execution, an installation summary is generated.

## Adding a New Step

The project includes a generator script to create new steps with the correct structure:

```bash
python generate_step.py step_name category "Step description" can_cleanup
```

For example:
```bash
python generate_step.py database_backup backup "Database backup operations" True
```

This creates:
- `src/steps/backup/__init__.py`
- `src/steps/backup/database_backup.py`
- `src/steps/backup/dependencies.py`
- `src/steps/backup/environment.py`

## Benefits of This Approach

1. **Modularity**: Each step is self-contained and can be developed, tested, and maintained independently.
2. **Flexibility**: Steps can be mixed and matched to create different deployment scenarios.
3. **Testability**: Each step can be tested in isolation without complex mocking.
4. **Simplicity**: New contributors can understand and modify individual steps without understanding the entire system.
5. **Maintainability**: Changes to one step don't affect others, reducing regression risks.
6. **Extensibility**: New steps can be added without changing existing code.
7. **Separation of concerns**: Dependencies, environment variables, and implementation logic are cleanly separated.
8. **Documentation**: Each aspect of a step is self-documenting through its file structure.

## CLI Commands

The management system provides the following commands:

- `kcmanage setup`: Initial setup and configuration
- `kcmanage deploy`: Deploy Keycloak with all required components
- `kcmanage status`: Check the status of Keycloak deployment
- `kcmanage backup`: Create a backup of Keycloak data
- `kcmanage restore`: Restore Keycloak from a backup

Each command imports and uses only the steps it needs, making the system more efficient and less prone to errors.