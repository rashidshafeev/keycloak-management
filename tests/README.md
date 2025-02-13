# Keycloak Configuration Testing

## Local Testing Setup

### 1. Prerequisites
```bash
# Start local Keycloak instance
docker-compose -f docker-compose.test.yml up -d

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

### 2. Test Structure
```
tests/
├── config/                     # Configuration tests
│   ├── test_authentication.py  # Authentication flow tests
│   ├── test_clients.py        # Client configuration tests
│   ├── test_events.py         # Event system tests
│   ├── test_integration.py    # Integration tests
│   └── test_config.yml        # Test configuration
├── data/                      # Test data
│   ├── realms/               # Realm configurations
│   ├── clients/              # Client configurations
│   └── users/                # Test user data
└── scripts/                  # Test utilities
    ├── setup_test_env.sh     # Environment setup
    └── cleanup_test_env.sh   # Environment cleanup
```

### 3. Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/config/test_authentication.py

# Run with coverage
pytest --cov=keycloak_management tests/
```

## Test Categories

### 1. Configuration Tests
- Schema validation
- CLI command validation
- Configuration file parsing
- Environment variable handling

### 2. Authentication Tests
- Authentication flow configuration
- Password policies
- MFA setup
- Social login configuration

### 3. Client Tests
- Client creation and configuration
- Protocol mapper setup
- Client scope configuration
- Service account setup

### 4. Event Tests
- Event listener configuration
- Event storage setup
- Webhook integration
- Event processing

### 5. Integration Tests
- End-to-end configuration
- Data synchronization
- Error handling
- Rollback scenarios

## Automated Test Suite

### 1. Unit Tests
```python
# tests/config/test_authentication.py
import pytest
from keycloak_management.config import AuthConfig

def test_auth_flow_configuration():
    config = AuthConfig.from_yaml("test_config.yml")
    assert config.validate() is True
    assert config.auth_flow.type == "browser"
    # Add more assertions
```

### 2. Integration Tests
```python
# tests/config/test_integration.py
import pytest
from keycloak_management import KeycloakManager

@pytest.mark.asyncio
async def test_full_configuration():
    manager = KeycloakManager()
    await manager.configure_from_yaml("test_config.yml")
    # Verify configuration
    assert await manager.verify_configuration()
```

### 3. Configuration Tests
```python
# tests/config/test_clients.py
import pytest
from keycloak_management.config import ClientConfig

def test_client_configuration():
    config = ClientConfig.from_yaml("test_config.yml")
    assert config.validate_client_urls()
    assert config.validate_protocol_mappers()
    # Add more assertions
```

## Running Locally

1. Start test environment:
```bash
./tests/scripts/setup_test_env.sh
```

2. Run test suite:
```bash
pytest --cov=keycloak_management tests/
```

3. View test coverage:
```bash
coverage report
coverage html  # For detailed HTML report
```

4. Cleanup:
```bash
./tests/scripts/cleanup_test_env.sh
```

## Test Configuration Example

```yaml
# tests/config/test_config.yml
realm:
  name: "test-realm"
  enabled: true
  displayName: "Test Realm"
  
clients:
  - clientId: "test-client"
    name: "Test Client"
    protocol: "openid-connect"
    enabled: true
    publicClient: false
    
authentication:
  flows:
    - alias: "browser"
      type: "basic-flow"
      description: "Browser based authentication"
      
events:
  enabled: true
  listeners:
    - "webhook"
  storage:
    type: "database"
    retention: "30d"
```
