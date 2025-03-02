from pathlib import Path
import os

def load_environment():
    """Initialize or load environment configuration"""
    env_file = Path('.env')
    
    # Load environment variables
    if env_file.exists():
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
        return env_vars
    else:
        return {}