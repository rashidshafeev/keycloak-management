import pytest
from unittest.mock import MagicMock, patch
from keycloak.config.clients import ClientConfigStep
from keycloak.config.validation import ValidationError

@pytest.fixture
def client_config():
    return {
        'clients': [
            {
                'clientId': 'test-client',
                'name': 'Test Client',
                'protocol': 'openid-connect',
                'enabled': True,
                'publicClient': False,
                'standardFlowEnabled': True,
                'implicitFlowEnabled': False,
                'directAccessGrantsEnabled': True,
                'serviceAccountsEnabled': True,
                'redirectUris': ['https://test.com/*']
            }
        ]
    }

@pytest.fixture
def client_step():
    step = ClientConfigStep()
    step.kcadm = MagicMock()
    return step

def test_validate_valid_config(client_step, client_config):
    """Test validation with valid configuration."""
    assert client_step.validate(client_config) is True

def test_validate_invalid_clients(client_step):
    """Test validation with invalid clients configuration."""
    config = {
        'clients': 'not-a-list'  # Should be a list
    }
    with pytest.raises(ValidationError, match="Clients configuration must be a list"):
        client_step.validate(config)

def test_validate_invalid_client_id(client_step):
    """Test validation with invalid client ID."""
    config = {
        'clients': [
            {
                'clientId': 123,  # Should be a string
                'protocol': 'openid-connect'
            }
        ]
    }
    with pytest.raises(ValidationError, match="Client ID must be a string"):
        client_step.validate(config)

def test_validate_invalid_protocol(client_step):
    """Test validation with invalid protocol."""
    config = {
        'clients': [
            {
                'clientId': 'test-client',
                'protocol': 'invalid-protocol'  # Should be openid-connect or saml
            }
        ]
    }
    with pytest.raises(ValidationError, match="Client protocol must be either 'openid-connect' or 'saml'"):
        client_step.validate(config)

def test_execute_creates_new_client(client_step, client_config):
    """Test execution creates new client when it doesn't exist."""
    client_step.kcadm.get.return_value = []
    client_step.execute(client_config)
    
    client_step.kcadm.create.assert_called_once()
    create_args = client_step.kcadm.create.call_args[0]
    assert create_args[0] == 'clients'
    assert create_args[1]['clientId'] == 'test-client'

def test_execute_updates_existing_client(client_step, client_config):
    """Test execution updates existing client."""
    existing_client = [{'id': '123', 'clientId': 'test-client'}]
    client_step.kcadm.get.return_value = existing_client
    client_step.execute(client_config)
    
    client_step.kcadm.update.assert_called_once()
    update_args = client_step.kcadm.update.call_args[0]
    assert update_args[0] == 'clients/123'

def test_get_existing_client(client_step):
    """Test getting existing client."""
    existing_client = [{'id': '123', 'clientId': 'test-client'}]
    client_step.kcadm.get.return_value = existing_client
    
    result = client_step._get_existing_client('test-client')
    assert result == existing_client[0]
    client_step.kcadm.get.assert_called_once_with('clients?clientId=test-client')
