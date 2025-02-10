import subprocess
import os
from pathlib import Path
from .base import DeploymentStep
import logging

class DatabaseBackupStep(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("database_backup", can_cleanup=False)
        self.config = config
        # Read backup configuration from the "database" section.
        self.backup_config = config.get("database", {}).get("backup", {})

    def check_completed(self) -> bool:
        # Always configure scheduled backup (idempotence is handled by cron file overwrite).
        return False

    def execute(self) -> bool:
        try:
            backup_enabled = self.config.get("backup", {}).get("enabled", False)
            if backup_enabled:
                # Path to the backup script that will perform the pg_dump.
                backup_script = "/opt/fawz/keycloak/scripts/db_backup.sh"
                # Get the schedule from the "database" backup config (default to 0 2 * * * if not set).
                schedule = self.backup_config.get("schedule", "0 2 * * *")
                cron_file = Path("/etc/cron.d/db-backup")
                # Compose cron job line; log output will go to /var/log/db_backup.log.
                backup_cmd = f"root {backup_script} >> /var/log/db_backup.log 2>&1"
                cron_line = f"{schedule} {backup_cmd}\n"
                cron_file.write_text(cron_line)
                os.chmod(cron_file, 0o644)
                self.logger.info(f"Database backup cron job configured with schedule: {schedule}")
            else:
                self.logger.info("Database backup is disabled in configuration.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure database backup: {e}")
            return False
