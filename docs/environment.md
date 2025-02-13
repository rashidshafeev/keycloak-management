# Environment Variables Documentation

This document describes all environment variables used in the Keycloak Management System.

## Core Configuration

### Keycloak
- `KEYCLOAK_ADMIN`: Admin username for Keycloak (default: admin)
- `KEYCLOAK_ADMIN_PASSWORD`: Admin password for Keycloak
- `KEYCLOAK_DB_PASSWORD`: Password for Keycloak database

### Docker
- `DOCKER_REGISTRY`: Docker registry to use (default: docker.io)
- `KEYCLOAK_VERSION`: Keycloak image version (default: latest)
- `POSTGRES_VERSION`: PostgreSQL image version (default: latest)

### SSL
- `SSL_CERT_PATH`: Path to SSL certificate file
- `SSL_KEY_PATH`: Path to SSL private key file

## Monitoring Configuration

### Prometheus
- `PROMETHEUS_SCRAPE_INTERVAL`: How frequently to scrape targets (default: 15s)
- `PROMETHEUS_EVAL_INTERVAL`: How frequently to evaluate rules (default: 15s)
- `PROMETHEUS_RETENTION_TIME`: How long to retain data (default: 15d)
- `PROMETHEUS_STORAGE_SIZE`: Maximum storage size for metrics (default: 50GB)

### Grafana
- `GRAFANA_ADMIN_USER`: Admin username for Grafana (default: admin)
- `GRAFANA_ADMIN_PASSWORD`: Admin password for Grafana

#### SMTP Configuration
- `GRAFANA_SMTP_ENABLED`: Enable SMTP for email alerts (default: true)
- `GRAFANA_SMTP_HOST`: SMTP server hostname
- `GRAFANA_SMTP_PORT`: SMTP server port (default: 587)
- `GRAFANA_SMTP_USER`: SMTP username
- `GRAFANA_SMTP_PASSWORD`: SMTP password
- `GRAFANA_SMTP_FROM`: From email address for alerts

#### Alert Notifications
- `GRAFANA_ALERT_EMAIL`: Email address to receive alerts
- `GRAFANA_SLACK_WEBHOOK_URL`: Slack webhook URL for alerts
- `GRAFANA_SLACK_CHANNEL`: Slack channel for alerts (default: #alerts)

## Security Configuration

### Wazuh
- `WAZUH_MANAGER_IP`: IP address of Wazuh manager (default: localhost)
- `WAZUH_REGISTRATION_PASSWORD`: Password for agent registration
- `WAZUH_AGENT_NAME`: Name for this Wazuh agent

### Firewall
- `FIREWALL_MAX_BACKUPS`: Number of firewall config backups to keep (default: 5)
- `FIREWALL_ALLOWED_PORTS`: Comma-separated list of allowed ports
- `FIREWALL_ADMIN_IPS`: Comma-separated list of admin IPs

## System Configuration

### Backup
- `BACKUP_RETENTION_DAYS`: Days to keep backups (default: 30)
- `BACKUP_STORAGE_PATH`: Path to store backups

### Logging
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format (default: json)
- `LOG_MAX_SIZE`: Maximum size of log files (default: 100MB)
- `LOG_MAX_FILES`: Number of log files to keep (default: 10)

## Usage

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the values in `.env` according to your environment:
   ```bash
   vim .env
   ```

3. The system will automatically load these variables during deployment.
