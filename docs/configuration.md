# Keycloak Configuration Guide

## Overview
This guide describes the configuration system for the Keycloak deployment. The system uses a combination of environment variables and YAML configuration files to provide:
- Easy-to-read and modify configuration
- Strong validation and error handling
- Rollback capabilities
- Secure credential management

## Configuration Structure

### 1. Environment Variables (.env)
The main configuration is done through environment variables defined in `.env`. Copy `.env.example` to create your configuration:

```bash
cp .env.example .env
```

Configuration sections:

#### Core Settings
- `KEYCLOAK_ADMIN`: Admin username
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password
- `KEYCLOAK_CLIENT_SECRET`: Default client secret

#### Database
- `POSTGRES_PASSWORD`: Database root password
- `DB_DATABASE`: Keycloak database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password

#### Docker
- `DOCKER_REGISTRY`: Container registry
- `KEYCLOAK_VERSION`: Keycloak image version
- `POSTGRES_VERSION`: PostgreSQL version

#### SSL/TLS
- `SSL_CERT_PATH`: Certificate path
- `SSL_KEY_PATH`: Private key path
- `SSL_EMAIL`: Admin email for certificates
- `SSL_DOMAINS`: Domain names

#### Monitoring
- `PROMETHEUS_SCRAPE_INTERVAL`: Metrics collection interval
- `PROMETHEUS_RETENTION_TIME`: Data retention period
- `GRAFANA_ADMIN_PASSWORD`: Grafana admin password

#### Notifications
- SMTP settings for email
- Twilio settings for SMS
- Webhook configuration for events

### 2. YAML Configuration Files
Located in `config/templates/`, these files define specific aspects of Keycloak:

#### Authentication (authentication.yml)
```yaml
flows:
  browser:
    type: basic-flow
    requirements:
      - cookie
      - kerberos
      - form
```

#### Events (events.yml)
```yaml
events:
  listeners:
    - name: "jboss-logging"
      enabled: true
    - name: "webhook"
      enabled: true
      properties:
        url: "${EVENT_WEBHOOK_URL}"
        secret: "${EVENT_WEBHOOK_SECRET}"
```

#### Security (security.yml)
```yaml
security:
  passwordPolicy:
    - type: "length"
      value: 8
    - type: "complexity"
      value: 3
  bruteForce:
    maxFailureWaitSeconds: 900
    failureFactor: 3
```

## Deployment Flow

1. **System Preparation**
   - Environment validation
   - Dependency checks
   - Network setup

2. **Infrastructure Setup**
   - Docker configuration
   - SSL certificate management
   - Database initialization

3. **Keycloak Deployment**
   - Container orchestration
   - Health checks
   - Initial configuration

4. **Post-Deployment**
   - Monitoring setup
   - Backup configuration
   - Security hardening

## Best Practices

1. **Security**
   - Never commit `.env` file
   - Use strong passwords
   - Regularly rotate secrets
   - Enable audit logging

2. **Monitoring**
   - Set up alerts for critical metrics
   - Monitor authentication failures
   - Track resource usage

3. **Backup**
   - Regular database backups
   - Configuration backups
   - Test restore procedures

4. **Updates**
   - Regular security updates
   - Staged rollouts
   - Maintain rollback plans

## Troubleshooting

1. **Container Issues**
   ```bash
   # Check container status
   docker ps -a | grep keycloak
   # View container logs
   docker logs keycloak
   ```

2. **Database Issues**
   ```bash
   # Check database connectivity
   docker exec postgres pg_isready
   # View database logs
   docker logs postgres
   ```

3. **SSL Issues**
   ```bash
   # Verify certificate
   openssl x509 -in $SSL_CERT_PATH -text -noout
   # Check certificate expiry
   openssl x509 -enddate -noout -in $SSL_CERT_PATH
   ```

## Support

For issues and support:
1. Check logs in `/var/log/keycloak/`
2. Review monitoring dashboards
3. Check container health status
4. Verify configuration values
