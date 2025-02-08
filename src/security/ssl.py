# /keycloak-management/src/security/ssl.py
from ..deployment.base import DeploymentStep
import subprocess
from pathlib import Path
import logging
from datetime import datetime
import OpenSSL.crypto
import shutil
import os

class CertificateManager(DeploymentStep):
    def __init__(self, config: dict):
        super().__init__("certificate_management", can_cleanup=False)
        self.config = config
        self.cert_dir = Path("/etc/letsencrypt/live")
        self.archive_dir = Path("/etc/letsencrypt/archive")
        self.main_domain = self.config["ssl"]["domains"][0]
        self.cert_path = self.cert_dir / self.main_domain / "fullchain.pem"
        self.key_path = self.cert_dir / self.main_domain / "privkey.pem"
        self.backup_dir = Path("/opt/fawz/keycloak/certs/backup")

    def _check_cert_validity(self, cert_path: Path) -> bool:
        """Check if certificate exists and is valid"""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, 
                cert_data
            )
            expiry = datetime.strptime(
                cert.get_notAfter().decode('ascii'), 
                '%Y%m%d%H%M%SZ'
            )
            # Check if cert expires in more than 30 days
            return (expiry - datetime.now()).days > 30
        except Exception as e:
            self.logger.debug(f"Certificate check failed: {e}")
            return False

    def _backup_existing_certs(self):
        """Backup existing certificates if present"""
        if self.cert_path.exists() and self.key_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(self.cert_path, backup_path / "fullchain.pem")
            shutil.copy2(self.key_path, backup_path / "privkey.pem")
            
            self.logger.info(f"Certificates backed up to {backup_path}")

    def _restore_latest_backup(self) -> bool:
        """Restore most recent certificate backup"""
        try:
            backup_dirs = sorted(self.backup_dir.glob('*'), reverse=True)
            if not backup_dirs:
                return False
                
            latest_backup = backup_dirs[0]
            shutil.copy2(latest_backup / "fullchain.pem", self.cert_path)
            shutil.copy2(latest_backup / "privkey.pem", self.key_path)
            self.logger.info(f"Restored certificates from {latest_backup}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore certificates: {e}")
            return False

    def check_completed(self) -> bool:
        """Check if valid certificates already exist"""
        return (self.cert_path.exists() and 
                self.key_path.exists() and 
                self._check_cert_validity(self.cert_path))

    def execute(self) -> bool:
        try:
            if self.check_completed():
                self.logger.info("Valid certificates already exist")
                return True

            self._backup_existing_certs()
            
            # Install certbot if needed
            subprocess.run([
                "apt-get", "install", "-y", "certbot"
            ], check=True)

            # Determine if we should use staging
            staging_arg = "--test-cert" if self.config["ssl"]["staging"] else ""
            
            domains_args = []
            for domain in self.config["ssl"]["domains"]:
                domains_args.extend(["-d", domain])

            # Request certificate
            try:
                subprocess.run([
                    "certbot", "certonly", "--standalone",
                    "--non-interactive", "--agree-tos",
                    f"--email={self.config['ssl']['email']}",
                    *domains_args,
                    staging_arg,
                    "--preferred-challenges", "http"
                ], check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to obtain certificates: {e}")
                # Try to restore backup if certificate request fails
                if self._restore_latest_backup():
                    self.logger.info("Restored previous certificates")
                    return True
                return False

            # Setup auto-renewal if configured
            if self.config["ssl"]["auto_renewal"]:
                renewal_cmd = "certbot renew --quiet --post-hook 'systemctl restart keycloak'"
                cron_file = Path("/etc/cron.d/certbot-renew")
                cron_file.write_text(f"0 0 1 * * root {renewal_cmd}\n")
                os.chmod(cron_file, 0o644)

            return True
            
        except Exception as e:
            self.logger.error(f"Certificate management failed: {e}")
            return False

# /keycloak-management/src/security/utils.py
def copy_certs_to_keycloak(cert_dir: Path, keycloak_cert_dir: Path):
    """Copy certificates to Keycloak directory with proper permissions"""
    keycloak_cert_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy and set proper permissions
    shutil.copy2(cert_dir / "fullchain.pem", keycloak_cert_dir / "tls.crt")
    shutil.copy2(cert_dir / "privkey.pem", keycloak_cert_dir / "tls.key")
    
    # Set permissions for Keycloak user
    os.chmod(keycloak_cert_dir / "tls.crt", 0o644)
    os.chmod(keycloak_cert_dir / "tls.key", 0o600)