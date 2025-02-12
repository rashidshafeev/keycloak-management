# Keycloak Configuration Guide

## Overview
The Keycloak configuration system uses YAML files for configuration and Python for validation and application. This provides:
- Easy-to-read and modify configuration files
- Strong validation and error handling
- Rollback capabilities
- Environment variable support

## Configuration Files
Configuration files are stored in `config/templates/` and follow this naming convention:
- `realm.yml` - Realm configuration
- `events.yml` - Events and listeners configuration
- `security.yml` - Security settings
- `users.yml` - User configuration
- `notifications.yml` - Notification settings

## Environment Variables
You can use environment variables in your YAML files using the `${VAR_NAME}` syntax:

```yaml
events:
  listeners:
    - name: "webhook"
      enabled: true
      properties:
        secret: "${WEBHOOK_SECRET}"
```

## Example Configurations

### Security Configuration (security.yml)
```yaml
security:
  passwordPolicy:
    - type: "length"
      value: 8
    - type: "digits"
      value: 1
    - type: "upperCase"
      value: 1
    - type: "specialChars"
      value: 1
  bruteForce:
    maxFailureWaitSeconds: 900
    waitIncrementSeconds: 60
    quickLoginCheckMilliSeconds: 1000
    minimumQuickLoginWaitSeconds: 60
    maxDeltaTimeSeconds: 43200
    failureFactor: 3
  session:
    ssoSessionIdleTimeout: 1800
    ssoSessionMaxLifespan: 36000
    offlineSessionIdleTimeout: 2592000
    accessTokenLifespan: 300
```

### Events Configuration (events.yml)
```yaml
events:
  listeners:
    - name: "jboss-logging"
      enabled: true
    - name: "webhook"
      enabled: true
      properties:
        url: "http://event-bus:3000/events"
        secret: "${EVENT_WEBHOOK_SECRET}"
        retries: 3
        timeout: 5000
  included_events:
    - LOGIN
    - LOGOUT
    - REGISTER
    - UPDATE_PROFILE
  admin_events:
    enabled: true
    include_representation: false
```

## Usage

### Command Line
```bash
# Configure all components
python deploy.py configure

# Configure specific component
python deploy.py configure --component events
```

### Interactive Mode
```bash
python deploy.py configure --interactive
```

## Error Handling
- Configuration validation errors will be logged with detailed messages
- Failed configurations will be automatically rolled back
- Each component maintains its own rollback history

## Best Practices
1. Always use version control for your YAML configurations
2. Test configuration changes in a non-production environment first
3. Use environment variables for sensitive values
4. Keep configurations modular and focused
5. Document any custom configurations in your team's documentation
