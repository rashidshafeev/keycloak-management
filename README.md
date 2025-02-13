# Keycloak Management System

Enterprise-grade Keycloak deployment solution with integrated monitoring, security, and management features.

## Features

- **Keycloak Management**
  - Automated deployment and configuration
  - Database management and backups
  - SSL/TLS support
  - High availability setup

- **Monitoring**
  - Prometheus metrics collection
  - Grafana dashboards
  - Alert management
  - Performance tracking

- **Security**
  - Firewall management
  - Wazuh security monitoring
  - Access control
  - Backup system

## System Requirements

### Minimum Requirements
- Ubuntu 20.04 LTS or later
- 4GB RAM
- 20GB SSD storage
- Root or sudo access

### Recommended Requirements
- 8GB RAM
- 40GB SSD storage
- Dedicated CPU cores

### Required Ports
| Port  | Service              | Protocol | Required |
|-------|---------------------|-----------|-----------|
| 22    | SSH                 | TCP       | Yes       |
| 80    | HTTP               | TCP       | Optional  |
| 443   | HTTPS              | TCP       | Optional  |
| 8080  | Keycloak HTTP      | TCP       | Yes       |
| 8443  | Keycloak HTTPS     | TCP       | Yes       |
| 3000  | Grafana            | TCP       | Yes       |
| 9090  | Prometheus         | TCP       | Yes       |
| 9100  | Node Exporter      | TCP       | Yes       |
| 9323  | Docker Metrics     | TCP       | Yes       |

## Installation Guide

### 1. Prepare Your VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install basic requirements
sudo apt install -y git python3 python3-pip docker.io docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
```

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/keycloak-management.git
cd keycloak-management

# Make install script executable
chmod +x install.sh

# Run installation script
sudo ./install.sh
```

### 3. Configure Environment

Edit `.env` with your settings. Here's a minimal production configuration:

```env
# Core Settings
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=StrongPassword123!     # Change this!
KEYCLOAK_DB_PASSWORD=SecureDbPass123!         # Change this!

# Domain Settings
KEYCLOAK_DOMAIN=keycloak.yourdomain.com       # Your domain
KEYCLOAK_PORT=8443

# SSL Settings (Optional, but recommended)
SSL_CERT_PATH=/etc/letsencrypt/live/keycloak.yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/keycloak.yourdomain.com/privkey.pem

# Monitoring Settings
GRAFANA_ADMIN_PASSWORD=GrafanaPass123!        # Change this!
GRAFANA_DOMAIN=grafana.yourdomain.com         # Your domain

# Alert Settings (Optional)
GRAFANA_SMTP_HOST=smtp.gmail.com
GRAFANA_SMTP_USER=your@email.com
GRAFANA_SMTP_PASSWORD=your_app_password
GRAFANA_ALERT_EMAIL=alerts@yourdomain.com

# Security Settings
FIREWALL_ALLOWED_PORTS=22,80,443,8080,8443,3000,9090
FIREWALL_ADMIN_IPS=YOUR.VPS.IP,YOUR.LOCAL.IP

# Backup Settings
BACKUP_RETENTION_DAYS=7
BACKUP_STORAGE_PATH=/opt/keycloak/backups
```

### 4. Run Installation

The installer will:
1. Deploy Keycloak with PostgreSQL
2. Setup Prometheus and Grafana
3. Configure security settings
4. Generate installation summary

### 5. Post-Installation

1. **Check Installation Summary**
   ```bash
   cat installation_summary.md
   ```
   This file contains all access URLs, credentials, and system status.

2. **Verify Services**
   ```bash
   # Check service status
   sudo systemctl status keycloak
   sudo systemctl status prometheus
   sudo systemctl status grafana-server
   ```

3. **Access Your Services**
   - Keycloak: https://keycloak.yourdomain.com:8443/auth/admin
   - Grafana: http://grafana.yourdomain.com:3000
   - Prometheus: http://your-vps-ip:9090 (internal access only)

4. **Security Steps**
   - Change all default passwords
   - Configure SSL certificates (Let's Encrypt recommended)
   - Review firewall rules
   - Setup regular backup verification

## Maintenance

### Backup Management

```bash
# Manual backup
sudo python3 backup.py

# View backups
ls -l /opt/keycloak/backups

# Verify backup
sudo python3 verify_backup.py
```

### Log Management

```bash
# View Keycloak logs
sudo journalctl -u keycloak -f

# View monitoring logs
sudo journalctl -u prometheus -f
sudo journalctl -u grafana-server -f
```

### Monitoring Dashboards

1. **Keycloak Dashboard**
   - Active sessions
   - Login attempts
   - Response times
   - Error rates

2. **System Dashboard**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u service-name -n 100 --no-pager
   
   # Check ports
   sudo netstat -tulpn | grep LISTEN
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **Monitoring Issues**
   ```bash
   # Check Prometheus targets
   curl localhost:9090/api/v1/targets
   
   # Check metrics
   curl localhost:9100/metrics
   ```

### Getting Help

1. Check `installation_summary.md` for system details
2. Review logs in `/var/log/fawz/keycloak/`
3. Open issues on GitHub with:
   - Error messages
   - Relevant logs
   - System information

## License

MIT License - see LICENSE file for details
