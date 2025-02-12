# Keycloak Management Tool

A comprehensive tool for managing Keycloak instances in development and production environments. This tool provides automated setup, configuration, monitoring, and maintenance capabilities for Keycloak deployments.

## Features

- 🚀 Automated Keycloak deployment with Docker
- 🔒 Security configuration and hardening
- 📜 SSL certificate management (Let's Encrypt integration)
- 🔄 Automated backup and restore
- 📊 Monitoring integration (Prometheus & Grafana)
- ✉️ Notification system (Email & SMS)
- 🌍 Multi-environment support
- 🔑 Realm and client management
- 👥 User and role management

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Access to target deployment server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/keycloak-management.git
cd keycloak-management
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# OR
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp config/.env.example config/.env
```

2. Configure the environment variables:

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| KEYCLOAK_ADMIN | Keycloak admin username | `admin` |
| KEYCLOAK_ADMIN_PASSWORD | Keycloak admin password | `adminpass123` |
| KEYCLOAK_DB_PASSWORD | Database password | `dbpass123` |
| KEYCLOAK_HOSTNAME | Keycloak hostname | `auth.example.com` |
| SSL_EMAIL | Email for SSL certificates | `admin@example.com` |

### Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| SMTP_HOST | SMTP server for notifications | `smtp.gmail.com` |
| SMTP_PORT | SMTP port | `587` |
| SMTP_USER | SMTP username | `notifications@example.com` |
| SMTP_PASSWORD | SMTP password | `smtppass123` |
| MONITORING_ENABLED | Enable Prometheus/Grafana | `true` |

## Usage

### Development Environment

```bash
python manage.py deploy --env development
```

### Production Environment

```bash
python manage.py deploy --env production
```

### Backup Management

```bash
# Create backup
python manage.py backup create

# List backups
python manage.py backup list

# Restore from backup
python manage.py backup restore <backup-id>
```

### Realm Management

```bash
# Create realm
python manage.py realm create <realm-name>

# Import realm configuration
python manage.py realm import <config-file>

# Export realm configuration
python manage.py realm export <realm-name>
```

## Project Structure

```
keycloak-management/
├── src/                    # Source code
│   ├── core/              # Core functionality
│   ├── commands/          # CLI commands
│   ├── config/            # Configuration management
│   ├── deploy/            # Deployment logic
│   ├── backup/            # Backup management
│   └── monitoring/        # Monitoring setup
├── config/                # Configuration files
│   ├── environments/      # Environment configs
│   └── templates/         # Config templates
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
