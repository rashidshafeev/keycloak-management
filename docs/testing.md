# Testing Environment

This document describes how to use the testing environment for the Keycloak Management project.

## Overview

The testing environment simulates a real Debian VPS deployment environment using Docker-in-Docker. It runs automated tests to verify the complete installation flow as it would occur on a real server.

## Security Considerations

### Git Credentials
The test environment uses Git credentials for repository access. These should be configured in `tests/deployment/.env`:
```
GIT_USERNAME=your_username
GIT_PASSWORD=your_password
```
⚠️ **IMPORTANT**: 
- Never commit the `.env` file to version control
- Add `.env` to `.gitignore`
- Use environment variables in CI/CD pipelines instead

## Test Structure

### Key Components
1. `Dockerfile.test` - Debian Bullseye-based container with:
   - Docker-in-Docker support
   - Systemd integration
   - Required dependencies
   - Line ending handling (dos2unix)

2. `docker-compose.test.yml` - Single service setup that simulates a VPS with:
   - Privileged mode for Docker-in-Docker
   - Volume mounts for Docker socket
   - Environment variable configuration
   - Port mappings

3. `test-entrypoint.sh` - Real-world deployment simulation:
   - Copies install.sh (simulating manual copy to VPS)
   - Runs installation with test parameters
   - Verifies services and commands
   - Tests reset functionality

### Test Cases

1. Environment Setup Test
   - Docker daemon initialization
   - System service configuration
   - Permission setup

2. Installation Flow Test
   - Install script copy simulation
   - Repository cloning
   - Dependency installation
   - Environment configuration

3. Service Deployment Test
   - Keycloak container deployment
   - Database initialization
   - Port availability
   - Service health checks

4. Command Installation Test
   - keycloak-deploy command creation
   - Command permissions
   - Command functionality

5. Reset and Cleanup Test
   - Complete system reset
   - Container cleanup
   - Volume removal
   - Directory cleanup

## Running Tests

### Prerequisites
- Docker
- Docker Compose
- Git access to the repository

### Configuration

1. Create environment file:
```bash
cd tests/deployment
cp .env.example .env  # Create from example if provided
```

2. Configure Git credentials in `.env`:
```properties
GIT_USERNAME=your_username
GIT_PASSWORD=your_password
```

### Basic Usage

1. Run complete test suite:
```bash
cd tests/deployment
docker-compose -f docker-compose.test.yml up --build
```

2. Clean up:
```bash
docker-compose -f docker-compose.test.yml down -v
```

### Port Mappings

The test environment maps the following ports:
- 28080: HTTP (Keycloak)
- 28443: HTTPS (Keycloak)
- 23000: Grafana
- 29090: Prometheus

### Debugging

1. Shell access:
```bash
docker exec -it deployment-vps-test-1 bash
```

2. View logs:
```bash
# Installation logs
docker exec deployment-vps-test-1 cat /var/log/keycloak-install.log

# Docker logs
docker exec deployment-vps-test-1 journalctl -u docker
```

3. Check services:
```bash
docker exec deployment-vps-test-1 systemctl status docker
```

### Common Issues

1. Docker-in-Docker Issues
   - Error: "Cannot connect to Docker daemon"
   - Solution: Check if Docker service is running inside container
   ```bash
   docker exec deployment-vps-test-1 systemctl status docker
   ```

2. Git Access Issues
   - Error: "Authentication failed for repository"
   - Solution: Verify .env credentials and repository access

3. Line Ending Issues
   - Error: "bad interpreter: No such file or directory"
   - Solution: Scripts are converted using dos2unix in Dockerfile

4. Volume Mount Issues
   - Error: "Cannot start service: failed to mount"
   - Solution: Ensure Docker socket permissions are correct

## CI/CD Integration

### GitLab CI Example
```yaml
test:
  variables:
    GIT_USERNAME: ${CI_DEPLOY_USER}
    GIT_PASSWORD: ${CI_DEPLOY_TOKEN}
  script:
    - cd tests/deployment
    - docker-compose -f docker-compose.test.yml up --build --exit-code-from vps-test
```

### GitHub Actions Example
```yaml
test:
  env:
    GIT_USERNAME: ${{ secrets.GIT_USERNAME }}
    GIT_PASSWORD: ${{ secrets.GIT_PASSWORD }}
  steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: |
        cd tests/deployment
        docker-compose -f docker-compose.test.yml up --build --exit-code-from vps-test
```

## Best Practices

1. Security
   - Never commit credentials
   - Use CI/CD secret management
   - Rotate test credentials regularly

2. Testing
   - Always use clean builds for testing
   - Verify all services are cleaned up after tests
   - Monitor resource usage during tests

3. Debugging
   - Check logs immediately when tests fail
   - Verify network connectivity
   - Ensure Docker daemon is running properly

## Adding New Tests

1. Modify `test-entrypoint.sh`:
   - Add new test cases
   - Include proper error handling
   - Add meaningful success/failure messages

2. Update `docker-compose.test.yml` if needed:
   - Add new services
   - Configure additional environment variables
   - Map new ports

3. Update Documentation:
   - Document new test cases
   - Update debugging section
   - Add new common issues if discovered
