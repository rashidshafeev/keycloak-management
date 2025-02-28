#!/usr/bin/env python3
"""
Step Generator Script

This script generates a new step module with the appropriate structure.
Usage: python generate_step.py step_name step_category
Example: python generate_step.py backup_step backup
"""

import os
import sys
from pathlib import Path
import textwrap

DEPENDENCIES_TEMPLATE = """import os
import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger("step.{step_name}.dependencies")

def check_{step_name}_dependencies() -> bool:
    \"\"\"
    Check if dependencies for the {step_description} step are installed
    
    Returns:
        bool: True if all dependencies are installed, False otherwise
    \"\"\"
    try:
        # Implement dependency checking
        # Example:
        # result = subprocess.run(['command', '--version'], 
        #                        check=False,
        #                        stdout=subprocess.PIPE, 
        #                        stderr=subprocess.PIPE,
        #                        text=True)
        # return result.returncode == 0
        
        # For now, we'll assume dependencies are installed
        return True
    except Exception as e:
        logger.error(f"Error checking dependencies: {{str(e)}}")
        return False

def install_{step_name}_dependencies() -> bool:
    \"\"\"
    Install dependencies for the {step_description} step
    
    Returns:
        bool: True if installation was successful, False otherwise
    \"\"\"
    try:
        # Implement dependency installation
        # Example:
        # subprocess.run(['apt-get', 'update'], check=True)
        # subprocess.run(['apt-get', 'install', '-y', 'package-name'], check=True)
        
        # Verify installation
        return check_{step_name}_dependencies()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: Command failed: {{e.cmd}}")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {{str(e)}}")
        return False
"""

ENVIRONMENT_TEMPLATE = """from typing import Dict, List
import logging

logger = logging.getLogger("step.{step_name}.environment")

def get_required_variables() -> List[Dict]:
    \"\"\"
    Define environment variables required by the {step_description} step
    
    Returns:
        List[Dict]: List of dictionaries defining required environment variables
    \"\"\"
    return [
        {{
            'name': 'EXAMPLE_VAR',
            'prompt': 'Example variable',
            'default': 'default-value'
        }},
        # Add more required variables here
    ]

def validate_variables(env_vars: Dict[str, str]) -> bool:
    \"\"\"
    Validate environment variables for the {step_description} step
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        bool: True if all variables are valid, False otherwise
    \"\"\"
    # Check if required variables are present
    required_vars = ['EXAMPLE_VAR']
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            logger.error(f"Required variable {{var}} is missing or empty")
            return False
    
    # Add additional validation if needed
    
    return True
"""

STEP_TEMPLATE = """from ...core.base import BaseStep
import os
from typing import Dict

# Import step-specific modules
from .dependencies import check_{step_name}_dependencies, install_{step_name}_dependencies
from .environment import get_required_variables, validate_variables

class {class_name}(BaseStep):
    \"\"\"Step for {step_description}\"\"\"
    
    def __init__(self):
        super().__init__("{step_name}", can_cleanup={can_cleanup})
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        \"\"\"Check if required dependencies are installed\"\"\"
        return check_{step_name}_dependencies()
    
    def _install_dependencies(self) -> bool:
        \"\"\"Install required dependencies\"\"\"
        return install_{step_name}_dependencies()
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        \"\"\"Execute the main deployment operation\"\"\"
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Implement the main deployment logic
            # Example:
            # example_var = env_vars.get('EXAMPLE_VAR', 'default-value')
            # self._run_command(['some-command', example_var])
            
            self.logger.info("Deployment successful")
            return True
        except Exception as e:
            self.logger.error(f"Deployment failed: {{str(e)}}")
            return False
    
    def _cleanup(self) -> None:
        \"\"\"Clean up after a failed deployment\"\"\"
        try:
            # Implement cleanup logic if can_cleanup=True
            # Example:
            # self._run_command(['cleanup-command'], check=False)
            pass
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {{str(e)}}")
"""

INIT_TEMPLATE = """from .{step_file} import {class_name}

__all__ = ['{class_name}']
"""

def convert_to_class_name(name):
    """Convert snake_case to CamelCase for class names"""
    parts = name.split('_')
    return ''.join(word.capitalize() for word in parts)

def convert_to_file_name(name):
    """Convert CamelCase to snake_case for file names"""
    if 'Step' in name:
        name = name.replace('Step', '')
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def create_step_module(step_name, category, description=None, can_cleanup=False):
    """Create a new step module with dependencies and environment files"""
    if not step_name.endswith('Step'):
        step_name = f"{step_name}Step"
    
    class_name = convert_to_class_name(step_name)
    file_name = convert_to_file_name(class_name)
    
    if description is None:
        description = f"{' '.join(file_name.split('_'))}"
    
    # Create directory structure
    base_dir = Path("src/steps") / category
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_path = base_dir / "__init__.py"
    if not init_path.exists():
        with open(init_path, "w") as f:
            f.write(INIT_TEMPLATE.format(step_file=file_name, class_name=class_name))
    else:
        # Append to existing __init__.py
        content = init_path.read_text()
        if f"from .{file_name}" not in content:
            with open(init_path, "a") as f:
                f.write(f"\nfrom .{file_name} import {class_name}\n")
                f.write(f"\n__all__ += ['{class_name}']\n")
    
    # Create the step file
    step_path = base_dir / f"{file_name}.py"
    if step_path.exists():
        print(f"Warning: File {step_path} already exists, not overwriting")
    else:
        with open(step_path, "w") as f:
            f.write(STEP_TEMPLATE.format(
                class_name=class_name,
                step_name=file_name,
                step_description=description,
                can_cleanup=str(can_cleanup).lower()
            ))
    
    # Create dependencies.py file
    dependencies_path = base_dir / "dependencies.py"
    if not dependencies_path.exists():
        with open(dependencies_path, "w") as f:
            f.write(DEPENDENCIES_TEMPLATE.format(
                step_name=file_name,
                step_description=description
            ))
    
    # Create environment.py file
    environment_path = base_dir / "environment.py"
    if not environment_path.exists():
        with open(environment_path, "w") as f:
            f.write(ENVIRONMENT_TEMPLATE.format(
                step_name=file_name,
                step_description=description
            ))
    
    print(f"Created step module:")
    print(f"  - Main step implementation: {step_path}")
    print(f"  - Dependencies module: {dependencies_path}")
    print(f"  - Environment module: {environment_path}")
    print(f"  - Updated/created: {init_path}")
    print(f"\nTo use this step, add the following to your kcmanage.py:")
    print(f"from src.steps.{category} import {class_name}")
    print(f"orchestrator.add_step({class_name}())")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_step.py step_name category [description] [can_cleanup]")
        print("Example: python generate_step.py backup_step backup \"Backing up the system\" True")
        sys.exit(1)
    
    step_name = sys.argv[1]
    category = sys.argv[2]
    
    description = None
    if len(sys.argv) > 3:
        description = sys.argv[3]
    
    can_cleanup = False
    if len(sys.argv) > 4:
        can_cleanup = sys.argv[4].lower() == "true"
    
    create_step_module(step_name, category, description, can_cleanup)