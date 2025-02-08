# src/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logging(log_dir: Path = Path("/opt/fawz/keycloak/logs")) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("keycloak_deployer")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_dir / "deployment.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger