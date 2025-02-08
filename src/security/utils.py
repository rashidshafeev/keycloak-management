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