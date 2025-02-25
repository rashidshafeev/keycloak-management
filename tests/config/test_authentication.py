import pytest
from unittest.mock import MagicMock, patch
from keycloak.config.authentication import AuthenticationConfigStep
from keycloak.config.validation import ValidationError

@pytest.fixture
def auth_config():
    return {
        'authentication': {
            'flows': [
                {
                    'alias': 'browser',
                    'providerId': 'basic-flow',
                    'description': 'Browser based authentication'
                }
            ],
            'requiredActions': [
                {
                    'alias': 'CONFIGURE_TOTP',
                    'name': 'Configure OTP',
                    'enabled': True,
                    'defaultAction': False
                }
            ]
        }
    }

@pytest.fixture
def auth_step():
    step = AuthenticationConfigStep()
    step.kcadm = MagicMock()
    return step

def test_validate_valid_config(auth_step, auth_config):
    """Test validation with valid configuration."""
    assert auth_step.validate(auth_config) is True

def test_validate_invalid_flows(auth_step):
    """Test validation with invalid flows configuration."""
    config = {
        'authentication': {
            'flows': 'not-a-list'  # Should be a list
        }
    }
    with pytest.raises(ValidationError, match="Authentication flows must be a list"):
        auth_step.validate(config)

def test_validate_invalid_flow_alias(auth_step):
    """Test validation with invalid flow alias."""
    config = {
        'authentication': {
            'flows': [
                {
                    'alias': 123,  # Should be a string
                    'providerId': 'basic-flow'
                }
            ]
        }
    }
    with pytest.raises(ValidationError, match="Flow alias must be a string"):
        auth_step.validate(config)

def test_validate_invalid_required_actions(auth_step):
    """Test validation with invalid required actions."""
    config = {
        'authentication': {
            'requiredActions': 'not-a-list'  # Should be a list
        }
    }
    with pytest.raises(ValidationError, match="Required actions must be a list"):
        auth_step.validate(config)

def test_execute_creates_new_flow(auth_step, auth_config):
    """Test execution creates new flow when it doesn't exist."""
    auth_step.kcadm.get.return_value = None
    auth_step.execute(auth_config)
    
    auth_step.kcadm.create.assert_called_once()
    create_args = auth_step.kcadm.create.call_args[0]
    assert create_args[0] == 'authentication/flows'
    assert create_args[1]['alias'] == 'browser'

def test_execute_updates_existing_flow(auth_step, auth_config):
    """Test execution updates existing flow."""
    existing_flow = {'id': '123', 'alias': 'browser'}
    auth_step.kcadm.get.return_value = existing_flow
    auth_step.execute(auth_config)
    
    auth_step.kcadm.update.assert_called_once()
    update_args = auth_step.kcadm.update.call_args[0]
    assert update_args[0] == 'authentication/flows/123'

def test_execute_configures_required_actions(auth_step, auth_config):
    """Test execution configures required actions."""
    auth_step.execute(auth_config)
    
    # Should try to get existing action
    auth_step.kcadm.get.assert_any_call('authentication/required-actions/CONFIGURE_TOTP')
    
    # Should create or update the action
    assert any(
        call[0][0] == 'authentication/required-actions'
        for call in auth_step.kcadm.create.call_args_list
    ) or any(
        'authentication/required-actions/CONFIGURE_TOTP' in call[0][0]
        for call in auth_step.kcadm.update.call_args_list
    )
