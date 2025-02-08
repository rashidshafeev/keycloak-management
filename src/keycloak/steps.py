# src/keycloak/cli/steps.py
import subprocess
import logging
from pathlib import Path
from typing import Optional
from ..deployment.base import DeploymentStep

class KeycloakCLIStep(DeploymentStep):
    def __init__(self, name: str, config: dict):
        super().__init__(name)
        self.config = config
        self.keycloak_home = Path("/opt/keycloak")
        self.kcadm = self.keycloak_home / "bin" / "kcadm.sh"
        self.logged_in = False

    def _login(self) -> bool:
        try:
            result = subprocess.run([
                str(self.kcadm),
                "config credentials",
                "--server", f"http://localhost:{self.config['keycloak']['http_port']}/auth",
                "--realm", "master",
                "--user", self.config['keycloak']['admin']['username'],
                "--password", self.config['keycloak']['admin']['password']
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logged_in = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

    def _run_cmd(self, *args: str) -> subprocess.CompletedProcess:
        if not self.logged_in and not self._login():
            raise Exception("Failed to login to Keycloak")
        
        return subprocess.run(
            [str(self.kcadm)] + list(args),
            capture_output=True,
            text=True,
            check=True
        )

class RealmConfigurationStep(KeycloakCLIStep):
    def __init__(self, config: dict):
        super().__init__("realm_configuration", config)

    def check_completed(self) -> bool:
        try:
            if not self._login():
                return False
            result = self._run_cmd(
                "get", f"realms/{self.config['keycloak']['realm']['name']}"
            )
            return result.returncode == 0
        except:
            return False

    def execute(self) -> bool:
        try:
            realm_config = Path(self.config['keycloak']['realm_config'])
            self._run_cmd("create", "realms", "-f", str(realm_config))
            return True
        except Exception as e:
            self.logger.error(f"Failed to create realm: {e}")
            return False

class ClientConfigurationStep(KeycloakCLIStep):
    def __init__(self, config: dict):
        super().__init__("client_configuration", config)

    def check_completed(self) -> bool:
        try:
            for client in self.config['keycloak']['clients']:
                result = self._run_cmd(
                    "get", "clients", 
                    "-r", self.config['keycloak']['realm']['name'],
                    "-q", f"clientId={client['clientId']}"
                )
                if not result.stdout.strip():
                    return False
            return True
        except:
            return False

    def execute(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            for client in self.config['keycloak']['clients']:
                try:
                    self._run_cmd(
                        "create", "clients",
                        "-r", realm_name,
                        "-f", str(Path(client['config_file']))
                    )
                except subprocess.CalledProcessError as e:
                    if "already exists" not in e.stderr:
                        raise
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure clients: {e}")
            return False

class EventConfigurationStep(KeycloakCLIStep):
    def __init__(self, config: dict):
        super().__init__("event_configuration", config)

    def check_completed(self) -> bool:
        try:
            result = self._run_cmd(
                "get", "events/config",
                "-r", self.config['keycloak']['realm']['name']
            )
            current_config = result.stdout
            return all(
                listener in current_config 
                for listener in self.config['keycloak']['eventsListeners']
            )
        except:
            return False

    def execute(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            listeners = ",".join(self.config['keycloak']['eventsListeners'])
            event_types = ",".join(self.config['keycloak']['enabledEventTypes'])

            self._run_cmd(
                "update", "events/config",
                "-r", realm_name,
                "-s", f"eventsListeners=[{listeners}]",
                "-s", f"enabledEventTypes=[{event_types}]",
                "-s", "eventsEnabled=true",
                "-s", "adminEventsEnabled=true",
                "-s", "adminEventsDetailsEnabled=true"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure events: {e}")
            return False

class UsersConfigurationStep(KeycloakCLIStep):
    def __init__(self, config: dict):
        super().__init__("users_configuration", config)

    def check_completed(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            users_file = Path(self.config['keycloak']['users_config'])
            if not users_file.exists():
                return True

            users = json.loads(users_file.read_text())
            for user in users:
                result = self._run_cmd(
                    "get", "users",
                    "-r", realm_name,
                    "-q", f"username={user['username']}"
                )
                if not result.stdout.strip():
                    return False
            return True
        except:
            return False

    def execute(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            users_file = Path(self.config['keycloak']['users_config'])
            
            if users_file.exists():
                self._run_cmd(
                    "create", "users",
                    "-r", realm_name,
                    "-f", str(users_file)
                )
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure users: {e}")
            return False

class WebhookConfigurationStep(KeycloakCLIStep):
    def __init__(self, config: dict):
        super().__init__("webhook_configuration", config)

    def check_completed(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            result = self._run_cmd(
                "get", "components",
                "-r", realm_name,
                "-q", "name=webhook-event-listener"
            )
            return bool(result.stdout.strip())
        except:
            return False

    def execute(self) -> bool:
        try:
            realm_name = self.config['keycloak']['realm']['name']
            webhook_config = self.config['keycloak']['webhook']

            self._run_cmd(
                "create", "components",
                "-r", realm_name,
                "-s", "name=webhook-event-listener",
                "-s", "providerId=webhook",
                "-s", "providerType=org.keycloak.events.EventListenerProviderFactory",
                "-s", f"config.url=[{webhook_config['url']}]",
                "-s", "config.headers=[Content-Type: application/json]",
                "-s", f"config.events=[{','.join(webhook_config['events'])}]"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure webhook: {e}")
            return False
