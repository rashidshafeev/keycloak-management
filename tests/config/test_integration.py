import pytest
import yaml
from unittest.mock import MagicMock, patch
from keycloak.config.configuration import ConfigurationManager
from keycloak.config.yaml_loader import YamlConfigLoader

@pytest.fixture
def config_file(tmp_path):
    """Create a temporary test configuration file."""
    config_path = tmp_path / "test_config.yml"
    with open("tests/config/test_config.yml", "r") as f:
        config_content = f.read()
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture
def mock_kcadm():
    """Create a mock KcAdm instance."""
    mock = MagicMock()
    # Mock successful authentication
    mock.authenticate.return_value = True
    # Mock getting realm
    mock.get.side_effect = lambda path: None if "realms/test-realm" in path else []
    return mock

@pytest.fixture
def config_manager(mock_kcadm):
    """Create a ConfigurationManager instance with mocked KcAdm."""
    manager = ConfigurationManager()
    manager.kcadm = mock_kcadm
    return manager

def test_load_config(config_file):
    """Test loading configuration from file."""
    loader = YamlConfigLoader()
    config = loader.load_config(config_file)
    
    assert config["realm"]["name"] == "test-realm"
    assert len(config["security"]["passwordPolicy"]) == 4
    assert len(config["clients"]) == 1
    assert len(config["roles"]) == 1
    assert len(config["authentication"]["flows"]) == 1
    assert len(config["events"]["listeners"]) == 2

def test_validate_config(config_manager, config_file):
    """Test validating configuration."""
    loader = YamlConfigLoader()
    config = loader.load_config(config_file)
    
    assert config_manager.validate(config) is True

def test_apply_config(config_manager, config_file):
    """Test applying configuration."""
    loader = YamlConfigLoader()
    config = loader.load_config(config_file)
    
    assert config_manager.apply(config) is True
    
    # Verify realm creation
    config_manager.kcadm.create.assert_any_call(
        "realms",
        {
            "realm": "test-realm",
            "enabled": True,
            "displayName": "Test Realm",
            "loginTheme": "keycloak",
            "accountTheme": "keycloak",
            "adminTheme": "keycloak",
            "emailTheme": "keycloak"
        }
    )
    
    # Verify client creation
    config_manager.kcadm.create.assert_any_call(
        "clients",
        {
            "clientId": "test-client",
            "name": "Test Client",
            "protocol": "openid-connect",
            "enabled": True,
            "publicClient": False,
            "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "redirectUris": ["https://test.com/*"],
            "webOrigins": ["https://test.com"]
        }
    )
    
    # Verify role creation
    config_manager.kcadm.create.assert_any_call(
        "roles",
        {
            "name": "test-role",
            "description": "Test role",
            "composite": False
        }
    )
    
    # Verify authentication flow creation
    config_manager.kcadm.create.assert_any_call(
        "authentication/flows",
        {
            "alias": "test-browser",
            "providerId": "basic-flow",
            "description": "Test browser based authentication",
            "topLevel": True,
            "builtIn": False
        }
    )
    
    # Verify event listener configuration
    config_manager.kcadm.update.assert_any_call(
        "events/config",
        {
            "eventsExpiration": 7200,
            "eventsListeners": ["email"]
        }
    )

def test_rollback_on_failure(config_manager, config_file):
    """Test configuration rollback on failure."""
    loader = YamlConfigLoader()
    config = loader.load_config(config_file)
    
    # Make client creation fail
    config_manager.kcadm.create.side_effect = [
        True,  # realm creation succeeds
        Exception("Failed to create client")  # client creation fails
    ]
    
    assert config_manager.apply(config) is False
    
    # Verify realm deletion during rollback
    config_manager.kcadm.delete.assert_called_with("realms/test-realm")
