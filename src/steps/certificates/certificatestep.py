from ...core.base import BaseStep
import subprocess
import logging
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import OpenSSL.crypto
import shutil
import re

# Import step-specific modules
from .dependencies import check_certificatestep_dependencies, install_certificatestep_dependencies
from .environment import get_required_variables, validate_variables

class CertificateStep(BaseStep):
    """Step for managing SSL/TLS certificates"""
    
    def __init__(self):
        super().__init__("certificate_management", can_cleanup=True)
        # Define the environment variables required by this step
        self.required_vars = get_required_variables()
        
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        return check_certificatestep_dependencies()
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        return install_certificatestep_dependencies()
    
    def _validate_certificate(self, cert_path: Path, domains: list) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Comprehensive certificate validation
        
        Args:
            cert_path: Path to the certificate file
            domains: List of domains to validate against
            
        Returns:
            Tuple of (is_valid, error_message, expiry_date)
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
            min_days = int(self.config.get('SSL_MIN_DAYS_VALID', '30'))
            if (expiry - datetime.now()).days <= min_days:
                return False, f"Certificate expires in less than {min_days} days", expiry
                
            # Verify certificate matches domains
            cert_domains = []
            for i in range(cert.get_extension_count()):
                ext = cert.get_extension(i)
                if ext.get_short_name() == b'subjectAltName':
                    cert_domains = str(ext).split(',')
                    cert_domains = [d.strip().split(':')[1] for d in cert_domains]
                    
            if not any(domain in cert_domains for domain in domains):
                return False, "Certificate domains don't match configuration", expiry
                
            # Verify key matches certificate
            key_path = cert_path.parent / "privkey.pem"
            try:
                with open(key_path, 'rb') as f:
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
        """
        Verify the certificate chain
        
        Args:
            cert_path: Path to the certificate chain file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
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
    
    def _manage_backups(self, cert_dir: Path, backup_dir: Path, domains: list) -> Optional[Path]:
        """
        Manage certificate backups with rotation
        
        Args:
            cert_dir: Directory containing the certificates
            backup_dir: Directory for backups
            domains: List of domains for validation
            
        Returns:
            Path to the new backup directory if successful, None otherwise
        """
        try:
            # List and sort backups by date
            backups = sorted(backup_dir.glob('*'))
            max_backups = int(self.config.get('SSL_MAX_BACKUPS', '5'))
            
            # Remove old backups if we exceed max_backups
            while len(backups) >= max_backups:
                oldest = backups.pop(0)
                shutil.rmtree(oldest)
                self.logger.info(f"Removed old backup: {oldest}")
                
            # Create new backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / timestamp
            backup_path.mkdir(parents=True, exist_ok=True)
            
            cert_path = cert_dir / domains[0] / "fullchain.pem"
            key_path = cert_dir / domains[0] / "privkey.pem"
            
            if cert_path.exists() and key_path.exists():
                shutil.copy2(cert_path, backup_path / "fullchain.pem")
                shutil.copy2(key_path, backup_path / "privkey.pem")
                
                # Store validation info
                is_valid, error_msg, expiry = self._validate_certificate(cert_path, domains)
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
    
    def _restore_backup(self, backup_path: Path, cert_dir: Path, domains: list) -> bool:
        """
        Restore certificate backup
        
        Args:
            backup_path: Path to the backup directory
            cert_dir: Target directory for restored certificates
            domains: List of domains for validation
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            # Verify backup before restoring
            backup_cert = backup_path / "fullchain.pem"
            is_valid, error_msg, _ = self._validate_certificate(backup_cert, domains)
            if not is_valid:
                self.logger.error(f"Backup validation failed: {error_msg}")
                return False
                
            # Restore certificates
            target_dir = cert_dir / domains[0]
            target_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(backup_path / "fullchain.pem", target_dir / "fullchain.pem")
            shutil.copy2(backup_path / "privkey.pem", target_dir / "privkey.pem")
            
            self.logger.info(f"Restored certificates from {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def _copy_certs_to_keycloak(self, cert_dir: Path, keycloak_cert_dir: Path) -> bool:
        """
        Copy certificates to Keycloak directory with proper permissions
        
        Args:
            cert_dir: Source directory containing certificates
            keycloak_cert_dir: Target Keycloak certificate directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keycloak_cert_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy and set proper permissions
            shutil.copy2(cert_dir / "fullchain.pem", keycloak_cert_dir / "tls.crt")
            shutil.copy2(cert_dir / "privkey.pem", keycloak_cert_dir / "tls.key")
            
            # Set permissions for Keycloak user
            os.chmod(keycloak_cert_dir / "tls.crt", 0o644)
            os.chmod(keycloak_cert_dir / "tls.key", 0o600)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy certificates to Keycloak: {e}")
            return False
    
    def _deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute certificate management operations"""
        # Validate environment variables
        if not validate_variables(env_vars):
            self.logger.error("Environment validation failed")
            return False
            
        try:
            # Set up paths and configuration
            cert_dir = Path(env_vars.get('SSL_CERT_DIR', '/etc/letsencrypt/live'))
            backup_dir = Path(env_vars.get('SSL_BACKUP_DIR', '/opt/keycloak/certs/backup'))
            domains = [d.strip() for d in env_vars['SSL_DOMAINS'].split(',')]
            main_domain = domains[0]
            
            cert_path = cert_dir / main_domain / "fullchain.pem"
            key_path = cert_dir / main_domain / "privkey.pem"
            
            # Check if we already have valid certificates
            if cert_path.exists() and key_path.exists():
                is_valid, error_msg, _ = self._validate_certificate(cert_path, domains)
                if is_valid:
                    chain_valid, chain_error = self._verify_cert_chain(cert_path)
                    if chain_valid:
                        self.logger.info("Valid certificates already exist")
                        return True
            
            # Create backup before making changes
            backup_path = self._manage_backups(cert_dir, backup_dir, domains)
            
            # Generate domains arguments for certbot
            domains_args = []
            for domain in domains:
                domains_args.extend(["-d", domain])
            
            # Request certificate
            try:
                staging_arg = ["--test-cert"] if env_vars.get('SSL_STAGING', 'true').lower() == 'true' else []
                
                self._run_command([
                    "certbot", "certonly", "--standalone",
                    "--non-interactive", "--agree-tos",
                    f"--email={env_vars['SSL_EMAIL']}",
                    *domains_args,
                    *staging_arg,
                    "--preferred-challenges", "http"
                ])
                
            except Exception as e:
                self.logger.error(f"Failed to obtain certificates: {e}")
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path, cert_dir, domains):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False
            
            # Verify the new certificates
            is_valid, error_msg, _ = self._validate_certificate(cert_path, domains)
            if not is_valid:
                self.logger.error(f"New certificate validation failed: {error_msg}")
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path, cert_dir, domains):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False
            
            # Verify the certificate chain
            chain_valid, chain_error = self._verify_cert_chain(cert_path)
            if not chain_valid:
                self.logger.error(f"New certificate chain validation failed: {chain_error}")
                if backup_path:
                    self.logger.info("Attempting to restore from backup...")
                    if self._restore_backup(backup_path, cert_dir, domains):
                        self.logger.info("Successfully restored from backup")
                        return True
                return False
            
            # Setup auto-renewal if configured
            if env_vars.get('SSL_AUTO_RENEWAL', 'true').lower() == 'true':
                renewal_cmd = (
                    "certbot renew --quiet "
                    "--pre-hook 'systemctl stop keycloak' "
                    "--post-hook 'systemctl start keycloak'"
                )
                cron_file = Path("/etc/cron.d/certbot-renew")
                with open(cron_file, 'w') as f:
                    f.write(f"0 0 1 * * root {renewal_cmd}\n")
                os.chmod(cron_file, 0o644)
                self.logger.info("Configured automatic certificate renewal")
            
            # Copy certificates to Keycloak
            keycloak_cert_dir = Path(env_vars.get('INSTALL_ROOT', '/opt/keycloak')) / 'certs'
            if not self._copy_certs_to_keycloak(cert_path.parent, keycloak_cert_dir):
                self.logger.error("Failed to copy certificates to Keycloak directory")
                return False
            
            self.logger.info("Certificate management completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Certificate management failed: {e}")
            if backup_path:
                self.logger.info("Attempting to restore from backup...")
                if self._restore_backup(backup_path, cert_dir, domains):
                    self.logger.info("Successfully restored from backup")
                    return True
            return False
    
    def _cleanup(self) -> None:
        """Clean up certificate files on failure"""
        try:
            # Only attempt cleanup if we know the domain
            if 'SSL_DOMAINS' in self.config:
                domains = [d.strip() for d in self.config['SSL_DOMAINS'].split(',')]
                main_domain = domains[0]
                cert_dir = Path(self.config.get('SSL_CERT_DIR', '/etc/letsencrypt/live'))
                domain_dir = cert_dir / main_domain
                
                if domain_dir.exists():
                    # Backup before cleanup
                    backup_dir = Path(self.config.get('SSL_BACKUP_DIR', '/opt/keycloak/certs/backup'))
                    self._manage_backups(cert_dir, backup_dir, domains)
                    
                    # Remove certificate files
                    shutil.rmtree(domain_dir, ignore_errors=True)
                    self.logger.info(f"Removed certificate directory: {domain_dir}")
                    
                # Also clean up Keycloak certificate directory
                keycloak_cert_dir = Path(self.config.get('INSTALL_ROOT', '/opt/keycloak')) / 'certs'
                if keycloak_cert_dir.exists():
                    shutil.rmtree(keycloak_cert_dir, ignore_errors=True)
                    self.logger.info(f"Removed Keycloak certificate directory: {keycloak_cert_dir}")
            
        except Exception as e:
            self.logger.warning(f"Certificate cleanup failed: {e}")
