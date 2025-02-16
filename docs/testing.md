# Testing Environment

This document describes how to use the testing environment for the Keycloak Management project.

## Overview

The testing environment uses Docker-in-Docker to simulate a real VPS deployment environment. It runs a series of automated tests to verify:
- Installation process
- Environment variable handling
- Docker container deployment
- Reset functionality

## Test Structure

The test environment consists of three main components:
1. `Dockerfile.test` - Defines the test container with Ubuntu 22.04 and Docker
2. `docker-compose.test.yml` - Orchestrates the test containers and networking
3. `test-entrypoint.sh` - Runs the actual test suite

### Test Cases

1. Fresh Installation
   - Verifies clean installation
   - Checks .env file creation
   - Validates required variables

2. Environment Configuration
   - Tests variable propagation
   - Validates default values
   - Checks configuration files

3. Docker Deployment
   - Verifies container creation
   - Checks service accessibility
   - Tests port mappings

4. Reset Functionality
   - Tests cleanup
   - Verifies backup creation
   - Checks container removal

## Running Tests

### Prerequisites
- Docker
- Docker Compose
- Git

### Basic Usage

1. Run all tests:
```bash
cd tests/deployment
docker-compose -f docker-compose.test.yml up --build
```

2. Clean up test environment:
```bash
docker-compose -f docker-compose.test.yml down
```

### Viewing Logs

1. View all logs in real-time:
```bash
docker-compose -f docker-compose.test.yml logs -f
```

2. View specific container logs:
```bash
# Main test container
docker-compose -f docker-compose.test.yml logs -f keycloak-test

# Database container
docker-compose -f docker-compose.test.yml logs -f postgres
```

3. View installation logs:
```bash
docker exec -it deployment-keycloak-test-1 cat /var/log/keycloak-install.log
```

4. View Docker daemon logs:
```bash
docker exec -it deployment-keycloak-test-1 cat /var/log/dockerd.log
```

### Test Ports

The test environment maps the following ports:
- 18080: HTTP (Keycloak)
- 18443: HTTPS (Keycloak)
- 13000: Grafana
- 19090: Prometheus

### Debugging

1. Access test container shell:
```bash
docker exec -it deployment-keycloak-test-1 bash
```

2. Check Docker status:
```bash
docker exec deployment-keycloak-test-1 docker ps
```

3. View environment variables:
```bash
docker exec deployment-keycloak-test-1 cat /opt/fawz/keycloak/.env
```

### Common Issues

1. Port conflicts
   - Error: "Bind for 0.0.0.0:xxxxx failed: port is already allocated"
   - Solution: Stop services using these ports or modify port mappings in docker-compose.test.yml

2. Docker-in-Docker issues
   - Error: "Cannot connect to the Docker daemon"
   - Solution: Check dockerd logs and ensure the daemon is running

3. Permission issues
   - Error: "Permission denied" or "Access denied"
   - Solution: Ensure the container is running with appropriate privileges (privileged: true)

## Adding New Tests

To add new test cases:
1. Edit `test-entrypoint.sh`
2. Add your test case with proper error handling
3. Update this documentation with any new test details

## CI/CD Integration

The test environment can be integrated into CI/CD pipelines:

```yaml
test:
  script:
    - cd tests/deployment
    - docker-compose -f docker-compose.test.yml up --build --exit-code-from keycloak-test
```

## Best Practices

1. Always clean up after testing:
```bash
docker-compose -f docker-compose.test.yml down -v
```

2. Use fresh builds for testing:
```bash
docker-compose -f docker-compose.test.yml build --no-cache
```

3. Monitor resource usage:
```bash
docker stats
```
