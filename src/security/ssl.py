from ..deployment.base import DeploymentStep
import subprocess
from pathlib import Path
import logging
from datetime import datetime, timedelta
import OpenSSL.crypto
import shutil
import os
from typing import Optional, Tuple, List
import re

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
        self.max_backups = self.config.get("ssl", {}).get("max_backups", 5)
        self.min_days_valid = self.config.get("ssl", {}).get("min_days_valid", 30)

    def _validate_certificate(self, cert_path: Path) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Comprehensive certificate validation
        Returns: (is_valid, error_message, expiry_date)
        """
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, 
                cert_data
            )
            
            # Check expiry
            expiry = datetime.strptime(
                cert.get_notAfter().decode('ascii'), 
                '%Y%m%d%H%M%SZ'
            )
            if (expiry - datetime.now()).days <= self.min_days_valid:
                return False, f"Certificate expires in less than {self.min_days_valid} days", expiry

            # Verify certificate matches domain
            cert_domains = []
            for i in range(cert.get_extension_count()):
                ext = cert.get_extension(i)
                if ext.get_short_name() == b'subjectAltName':
                    cert_domains = str(ext).split(',')
                    cert_domains = [d.strip().split(':')[1] for d in cert_domains]

            if not any(domain in cert_domains for domain in self.config["ssl"]["domains"]):
                return False, "Certificate domains don't match configuration", expiry

            # Verify key matches certificate
            try:
                with open(self.key_path, 'rb') as f:
                    key_data = f.read()
                key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key_data)
                context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
                context.use_privatekey(key)
                context.use_certificate(cert)
                context.check_privatekey()
            except Exception as e:
                return False, f"Private key validation failed: {e}", expiry

            return True, None, expiry
        except Exception as e:
            return False, f"Certificate validation failed: {e}", None

    def _verify_cert_chain(self, cert_path: Path) -> Tuple[bool, Optional[str]]:
        """Verify the certificate chain"""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            # Split the chain into individual certificates
            certs = []
            for cert_pem in re.findall(
                b'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',
                cert_data, re.DOTALL
            ):
                cert = OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_PEM,
                    cert_pem
                )
                certs.append(cert)

            if not certs:
                return False, "No certificates found in chain"

            # Verify each certificate in the chain
            store = OpenSSL.crypto.X509Store()
            for i in range(1, len(certs)):  # Skip the leaf certificate
                store.add_cert(certs[i])

            store_ctx = OpenSSL.crypto.X509StoreContext(store, certs[0])
            try:
                store_ctx.verify_certificate()
                return True, None
            except Exception as e:
                return False, f"Certificate chain verification failed: {e}"

        except Exception as e:
            return False, f"Chain verification failed: {e}"

    def _manage_backups(self):
        """Manage certificate backups with rotation"""
        try:
            # List and sort backups by date
            backups = sorted(self.backup_dir.glob('*'))
            
            # Remove old backups if we exceed max_backups
            while len(backups) >= self.max_backups:
                oldest = backups.pop(0)
                shutil.rmtree(oldest)
                self.logger.info(f"Removed old backup: {oldest}")

            # Create new backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            if self.cert_path.exists() and self.key_path.exists():
                shutil.copy2(self.cert_path, backup_path / "fullchain.pem")
                shutil.copy2(self.key_path, backup_path / "privkey.pem")
                
                # Store validation info
                is_valid, error_msg, expiry = self._validate_certificate(self.cert_path)
                info = {
                    "timestamp": timestamp,
                    "is_valid": is_valid,
                    "error_msg": error_msg,
                    "expiry": expiry.isoformat() if expiry else None
                }
                
                with open(backup_path / "backup_info.txt", 'w') as f:
                    for key, value in info.items():
                        f.write(f"{key}: {value}\n")
                
                self.logger.info(f"Created new backup at {backup_path}")
                return backup_path
        except Exception as e:
            self.logger.error(f"Backup management failed: {e}")
            return None

    def _restore_backup(self, specific_backup: Optional[Path] = None) -> bool:
        """Restore certificate backup"""
        try:
            if specific_backup and specific_backup.exists():
                backup_path = specific_backup
            else:
                backups = sorted(self.backup_dir.glob('*'), reverse=True)
                if not backups:
                    return False
                backup_path = backups[0]

            # Verify backup before restoring
            backup_cert = backup_path / "fullchain.pem"
            is_valid, error_msg, _ = self._validate_certificate(backup_cert)
            if not is_valid:
                self.logger.error(f"Backup validation failed: {error_msg}")
                return False

            # Restore certificates
            self.cert_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path / "fullchain.pem", self.cert_path)
            shutil.copy2(backup_path / "privkey.pem", self.key_path)
            
            self.logger.info(f"Restored certificates from {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False

    def check_completed(self) -> bool:
        """Check if valid certificates exist and are properly configured"""
        if not (self.cert_path.exists() and self.key_path.exists()):
            return False

        # Validate certificate
        is_valid, error_msg, _ = self._validate_certificate(self.cert_path)
        if not is_valid:
            self.logger.warning(f"Certificate validation failed: {error_msg}")
            return False

        # Verify certificate chain
        chain_valid, chain_error = self._verify_cert_chain(self.cert_path)
        if not chain_valid:
            self.logger.warning(f"Certificate chain validation failed: {chain_error}")
            return False

        return True

    def execute(self) -> bool:
        try:
            if self.check_completed():
                self.logger.info("Valid certificates already exist")
                return True

            # Create backup before making any changes
            backup_path = self._manage_backups()
            
            # Install certbot if needed
            try:
                subprocess.run([
                    "apt-get", "update"
                ], check=True)
                subprocess.run([
                    "apt-get", "install", "-y", "certbot"
                ], check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install certbot: {e}")
                return False

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
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False

            # Verify the new certificates
            is_valid, error_msg, _ = self._validate_certificate(self.cert_path)
            if not is_valid:
                self.logger.error(f"New certificate validation failed: {error_msg}")
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False

            # Verify the certificate chain
            chain_valid, chain_error = self._verify_cert_chain(self.cert_path)
            if not chain_valid:
                self.logger.error(f"New certificate chain validation failed: {chain_error}")
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False

            # Setup auto-renewal if configured
            if self.config["ssl"]["auto_renewal"]:
                renewal_cmd = (
                    "certbot renew --quiet "
                    "--pre-hook 'systemctl stop keycloak' "
                    "--post-hook 'systemctl start keycloak'"
                )
                cron_file = Path("/etc/cron.d/certbot-renew")
                cron_file.write_text(f"0 0 1 * * root {renewal_cmd}\n")
                os.chmod(cron_file, 0o644)
                self.logger.info("Configured automatic certificate renewal")

            self.logger.info("Certificate management completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Certificate management failed: {e}")
            if backup_path:
                self.logger.info("Attempting to restore from backup...")
                if self._restore_backup(backup_path):
                    self.logger.info("Successfully restored from backup")
                    return True
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