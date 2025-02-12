import pytest
from unittest.mock import MagicMock, patch
from keycloak.config.events import EventConfigStep
from keycloak.config.validation import ValidationError

@pytest.fixture
def event_config():
    return {
        'events': {
            'storage': {
                'expiration': 7200  # 2 hours in seconds
            },
            'listeners': [
                {
                    'name': 'email',
                    'type': 'email',
                    'enabled': True,
                    'properties': {
                        'events': ['LOGIN', 'LOGIN_ERROR', 'REGISTER']
                    }
                },
                {
                    'name': 'webhook',
                    'type': 'webhook',
                    'enabled': True,
                    'properties': {
                        'url': 'https://webhook.test.com',
                        'events': ['LOGIN', 'REGISTER']
                    }
                }
            ]
        }
    }

@pytest.fixture
def event_step():
    step = EventConfigStep()
    step.kcadm = MagicMock()
    return step

def test_validate_valid_config(event_step, event_config):
    """Test validation with valid configuration."""
    assert event_step.validate(event_config) is True

def test_validate_invalid_storage_expiration(event_step):
    """Test validation with invalid storage expiration."""
    config = {
        'events': {
            'storage': {
                'expiration': 'not-a-number'  # Should be an integer
            }
        }
    }
    with pytest.raises(ValidationError, match="Event storage expiration must be an integer"):
        event_step.validate(config)

def test_validate_invalid_listeners(event_step):
    """Test validation with invalid listeners configuration."""
    config = {
        'events': {
            'listeners': 'not-a-list'  # Should be a list
        }
    }
    with pytest.raises(ValidationError, match="Event listeners must be a list"):
        event_step.validate(config)

def test_validate_invalid_listener_enabled(event_step):
    """Test validation with invalid listener enabled flag."""
    config = {
        'events': {
            'listeners': [
                {
                    'name': 'email',
                    'enabled': 'not-a-boolean'  # Should be a boolean
                }
            ]
        }
    }
    with pytest.raises(ValidationError, match="Listener enabled flag must be boolean"):
        event_step.validate(config)

def test_validate_missing_listener_name(event_step):
    """Test validation with missing listener name."""
    config = {
        'events': {
            'listeners': [
                {
                    'enabled': True  # Missing name
                }
            ]
        }
    }
    with pytest.raises(ValidationError, match="Each listener must have a name"):
        event_step.validate(config)

def test_execute_configures_storage(event_step, event_config):
    """Test execution configures event storage."""
    event_step.execute(event_config)
    
    # Should update event config
    event_step.kcadm.update.assert_any_call(
        'events/config',
        {'eventsExpiration': 7200}
    )

def test_execute_configures_listeners(event_step, event_config):
    """Test execution configures event listeners."""
    event_step.execute(event_config)
    
    # Should configure email listener
    event_step.kcadm.update.assert_any_call(
        'events/config',
        {'eventsListeners': ['email']}
    )

def test_execute_configures_webhook(event_step, event_config):
    """Test execution configures webhook listener."""
    event_step.execute(event_config)
    
    # Should configure webhook
    webhook_config = event_config['events']['listeners'][1]
    event_step.kcadm.create.assert_any_call(
        'webhooks',
        {
            'name': webhook_config['name'],
            'url': webhook_config['properties']['url'],
            'events': webhook_config['properties']['events']
        }
    )
