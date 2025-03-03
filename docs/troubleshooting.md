# Keycloak Management Troubleshooting Guide

## Common Issues and Solutions

### OpenSSL Import Error

**Issue**: `No module named 'OpenSSL'` error when running commands

**Solution**: 
1. Ensure you have the OpenSSL development libraries installed:
   ```bash
   # Debian/Ubuntu
   apt-get update && apt-get install -y libssl-dev

   # RHEL/CentOS
   yum install -y openssl-devel
   ```

2. Reinstall the Python OpenSSL module:
   ```bash
   pip install pyOpenSSL
   ```

### Module Import Errors

**Issue**: Errors like `cannot import name 'CertificateStepstep'` or `module has no attribute 'KeycloakDeployStep'`

**Solution**:
1. These are class naming inconsistencies between the code that imports the classes and the actual class definitions.
2. Always check the actual class name in the implementation files:
   - Check `certificatestep.py` for the correct class name (`CertificateStep`)
   - Check `keycloak_deploymentstep.py` for the correct class name (`KeycloakDeploymentstep`)
3. Update the deployment script to use the correct class names

### Name Inconsistencies

Some common naming inconsistencies to watch for:

1. `CertificateStep` vs `CertificateStepstep`
2. `KeycloakDeployStep` vs `KeycloakDeploymentstep`
3. File names vs class names (e.g., `keycloak_deploymentstep.py` contains `KeycloakDeploymentstep`)

### Enhanced Debugging

If you encounter issues, enable verbose logging:

```bash
kcmanage deploy --verbose
```

For even more detailed information, check the log output in your deployment:

```bash
tail -f /var/log/keycloak-install.log
```

## Testing Environment Issues

When running in the test environment (`tests/deployment`), some additional issues might occur:

1. **Missing system packages**: The test container is minimal and might need additional packages:
   ```bash
   apt-get update && apt-get install -y libssl-dev python3-dev
   ```

2. **Environment variables not loaded**: The test environment might not have all required variables:
   ```bash
   cp .env.test /opt/fawz/keycloak/.env
   ```

3. **File permission issues**: Check permissions if you encounter access errors:
   ```bash
   chown -R root:root /opt/fawz/keycloak
   chmod -R 755 /opt/fawz/keycloak
   ```

## Coding Conventions

To avoid naming inconsistencies, follow these conventions:

1. Class names should match their file names (e.g., `certificatestep.py` → `CertificateStep`)
2. Keep class names consistent in all imports and references
3. Use consistent naming patterns across similar components (e.g., all deployment steps should follow the same naming pattern)

## Recent Fixes

We've recently fixed the following issues:

1. Fixed `src/steps/certificates/__init__.py` to correctly import `CertificateStep` instead of the misspelled `CertificateStepstep`

2. Updated `kcmanage/commands/deploy.py` to use the correct class name `KeycloakDeploymentstep` instead of the incorrect `KeycloakDeployStep`

3. Added better error handling in the deployment command to detect and report AttributeError when a class isn't found in a module
