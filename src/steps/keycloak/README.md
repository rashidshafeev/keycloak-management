# Keycloak Deployment Step

This module handles the deployment and configuration of Keycloak using Docker containers. It provides a complete setup including the PostgreSQL database, Keycloak server, and configuration management.

## Overview

The Keycloak deployment step performs the following operations:

1. **Dependency Management**: Checks and installs required dependencies (Docker, Docker Compose, Python Docker SDK)
2. **Container Configuration**: Sets up containers with appropriate resource limits and volume mounts
3. **Network Setup**: Creates a dedicated network for Keycloak and related services
4. **Database Deployment**: Deploys PostgreSQL with appropriate configuration
5. **Keycloak Deployment**: Deploys the Keycloak server container with optimized settings
6. **Configuration**: Applies realm and client configurations to the Keycloak instance

## Architecture

The deployment uses a containerized architecture with the following components:

```
┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │
│     Keycloak      │◄────►│    PostgreSQL     │
│     Container     │      │     Container     │
│                   │      │                   │
└───────┬───────────┘      └───────────────────┘
        │
        │
        ▼
┌───────────────────┐
│    Host System    │
│  (Port Mapping)   │
└───────┬───────────┘
        │
        │
        ▼
┌───────────────────┐
│     External      │
│      Access       │
└───────────────────┘
```

## Configuration Templates

The step uses several configuration templates located in the `config/templates` directory:

- **realm.yml**: Defines the realm configuration
- **clients.yml**: Defines client applications
- **roles.yml**: Defines realm-level and client-level roles
- **users.yml**: Defines users for testing or initial setup
- **authentication.yml**: Defines authentication flows and requirements

## Environment Variables

The step requires several environment variables to function correctly:

### Database Configuration
- `DB_NAME`: Keycloak database name (default: "keycloak")
- `DB_USER`: Keycloak database user (default: "keycloak")
- `DB_PASSWORD`: Keycloak database password (required)

### Admin Configuration
- `KEYCLOAK_ADMIN`: Admin username (default: "admin")
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password (required)

### Network Configuration
- `KEYCLOAK_FRONTEND_URL`: Keycloak frontend URL (default: "http://localhost:8080/auth")
- `KEYCLOAK_HTTP_PORT`: HTTP port mapping (default: "8080")
- `KEYCLOAK_HTTPS_PORT`: HTTPS port mapping (default: "8443")

### Resource Configuration
- `KEYCLOAK_MEM_LIMIT`: Keycloak memory limit (default: "2g")
- `KEYCLOAK_MEM_RESERVATION`: Keycloak memory reservation (default: "1g")
- `POSTGRES_MEM_LIMIT`: PostgreSQL memory limit (default: "1g")
- `POSTGRES_MEM_RESERVATION`: PostgreSQL memory reservation (default: "512m")

### Storage Configuration
- `KEYCLOAK_DATA_DIR`: Directory for Keycloak data (default: "/opt/fawz/keycloak/data")
- `POSTGRES_DATA_DIR`: Directory for PostgreSQL data (default: "/opt/fawz/keycloak/postgres-data")

## Deployment Process

The step follows this process to deploy Keycloak:

1. **Validation**: Validates all environment variables
2. **Configuration Preparation**: Prepares container configurations and environment variables
3. **Network Setup**: Ensures the Docker network exists
4. **Database Deployment**: Deploys PostgreSQL container
5. **Health Check**: Waits for PostgreSQL to become healthy
6. **Keycloak Deployment**: Deploys Keycloak container
7. **Readiness Check**: Waits for Keycloak to become ready
8. **Configuration Application**: Applies configuration to Keycloak

## Cleanup Process

If deployment fails, the step will perform the following cleanup operations:

1. Stop the Keycloak container (if it exists)
2. Remove the Keycloak container (if it exists)
3. Stop the PostgreSQL container (if it exists)
4. Remove the PostgreSQL container (if it exists)

## Troubleshooting

Common issues and their solutions:

1. **Container fails to start**: Check Docker logs with `docker logs keycloak` or `docker logs postgres`
2. **Database connection issues**: Ensure PostgreSQL container is healthy and network is properly configured
3. **Configuration errors**: Check Keycloak logs for detailed error messages
4. **Memory issues**: Adjust memory limits using environment variables
5. **Port conflicts**: Change port mappings if there are conflicts with existing services

## Security Considerations

Important security aspects:

1. Always use strong passwords for database and admin users
2. Consider using a reverse proxy for TLS termination in production
3. Use volume mounts to persist data and enable backup strategies
4. Restrict network access in production environments
5. Configure proper authentication flows for your security requirements