from ...core.base import BaseStep
import os
import subprocess
from pathlib import Path
from typing import Dict

# Import step-specific modules
from .dependencies import check_database_backupstep_dependencies, install_database_backupstep_dependencies
from .environment import get_required_variables, validate_variables

class DatabaseBackupStepstep(BaseStep):
    """Step for Database backup operations"""
    
    def __init__(self):
        super().__init__("database_backupstep", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_database_backupstep_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_database_backupstep_dependencies()
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute the main deployment operation"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Get backup script path relative to this module
            current_dir = Path(__file__).parent
            backup_script = current_dir / "scripts" / "db_backup.sh"
            
            # Ensure script is executable
            os.chmod(backup_script, 0o755)
            
            # Set up cron job for regular backups
            backup_schedule = env_vars.get('BACKUP_SCHEDULE', '0 2 * * *')  # Default: 2 AM daily
            backup_log = env_vars.get('BACKUP_LOG', '/var/log/db_backup.log')
            
            # Create cron configuration
            cron_content = f"{backup_schedule} root {backup_script} >> {backup_log} 2>&1\n"
            cron_file_path = Path("/etc/cron.d/db-backup")
            
            # Write cron file
            self.logger.info(f"Setting up cron job with schedule: {backup_schedule}")
            with open(cron_file_path, 'w') as cron_file:
                cron_file.write(cron_content)
            
            # Set proper permissions
            os.chmod(cron_file_path, 0o644)
            
            # Run initial backup if requested
            if env_vars.get('RUN_INITIAL_BACKUP', 'false').lower() == 'true':
                self.logger.info("Running initial backup...")
                subprocess.run([str(backup_script)], check=True)
            
            self.logger.info("Database backup configuration successfully deployed")
            return True
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return False
    
    def _cleanup(self) -> None:
        """Clean up after a failed deployment"""
        try:
            # Remove cron job if it was created
            cron_file_path = Path("/etc/cron.d/db-backup")
            if cron_file_path.exists():
                cron_file_path.unlink()
                self.logger.info("Removed backup cron job during cleanup")
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {str(e)}")
