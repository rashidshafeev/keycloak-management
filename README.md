# Keycloak Deployment Automation

An automated deployment tool for setting up production-ready Keycloak instances with proper security configurations, monitoring, and maintenance capabilities.

## Features

- Automated system preparation and security hardening
- Docker-based Keycloak deployment
- Automatic SSL certificate management via Let's Encrypt
- Firewall configuration with fail2ban integration
- Database backup management
- Email and SMS notification setup
- Monitoring setup (Prometheus & Grafana)
- Multi-environment support (staging/production)

## Prerequisites

- Ubuntu 20.04 or newer
- Python 3.8+
- Root access to the target server

## Quick Installation

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/keycloak-management/main/install.sh | sudo bash
```

## Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/keycloak-management.git
cd keycloak-management
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
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

2. Configure the required environment variables:

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| POSTGRES_PASSWORD | PostgreSQL database password | `strongpassword123` |
| KEYCLOAK_ADMIN_PASSWORD | Keycloak admin console password | `adminpass123` |
| KEYCLOAK_CLIENT_SECRET | Secret for secure client connections | `clientsecret123` |
| GRAFANA_ADMIN_PASSWORD | Grafana dashboard admin password | `grafanapass123` |
| SSL_EMAIL | Email for SSL certificate registration | `admin@example.com` |
| SSL_DOMAINS | Comma-separated list of domains | `auth.example.com` |
| SMTP_HOST | SMTP server hostname | `smtp.gmail.com` |
| SMTP_PORT | SMTP server port | `587` |
| SMTP_USER | SMTP authentication username | `your-email@gmail.com` |
| SMTP_PASSWORD | SMTP authentication password | `your-app-password` |
| SMTP_FROM | Email sender address | `noreply@yourdomain.com` |
| TWILIO_ACCOUNT_SID | Twilio account SID (for SMS) | `ACxxxxxxxxxxxxxxxx` |
| TWILIO_AUTH_TOKEN | Twilio authentication token | `your-auth-token` |
| TWILIO_FROM_NUMBER | Twilio sender phone number | `+1234567890` |

## Usage

1. Deploy to staging environment:
```bash
sudo keycloak-deploy --config config/environments/staging.yml
```

2. Deploy to production:
```bash
sudo keycloak-deploy --config config/environments/production.yml
```

## Development Guidelines

### Project Structure
```
keycloak-management/
├── src/
│   ├── deployment/     # Core deployment logic
│   ├── keycloak/      # Keycloak-specific configuration
│   ├── security/      # Security-related components
│   ├── system/        # System preparation and setup
│   └── utils/         # Utility functions and helpers
├── config/
│   ├── environments/  # Environment-specific configurations
│   └── templates/     # Configuration templates
```

### Adding New Features

1. **New Deployment Steps**
   - Create a new class inheriting from `DeploymentStep`
   - Implement required methods: `check_completed()`, `execute()`, `cleanup()`
   - Add the step to `DeploymentOrchestrator`

2. **Configuration Changes**
   - Add new configuration options to environment YAML files
   - Update configuration templates if needed
   - Add corresponding environment variables to `.env.example`

3. **Testing**
   - Write unit tests for new components
   - Test in staging environment before production
   - Verify cleanup procedures work correctly

### Code Style Guidelines

1. **Python Standards**
   - Follow PEP 8 guidelines
   - Use type hints for function arguments and returns
   - Document classes and methods using docstrings

2. **Error Handling**
   - Implement proper error handling and logging
   - Ensure cleanup procedures for failure scenarios
   - Maintain idempotency in deployment steps

3. **Security Practices**
   - Never commit sensitive data or credentials
   - Use environment variables for sensitive information
   - Implement proper permission checks

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For support, please open an issue on the GitHub repository or contact the maintainers.
