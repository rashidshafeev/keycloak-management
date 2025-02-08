# /keycloak-management/src/keycloak/config/base.py
class BaseConfigurator:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.logger = logging.getLogger(f"keycloak_config.{self.__class__.__name__}")

    def _load_config_file(self, filename: str) -> dict:
        """Load configuration from file if exists"""
        config_file = self.config_dir / filename
        if config_file.exists():
            return json.loads(config_file.read_text())
        return {}

    def _get_env_value(self, key: str, default: str = None) -> str:
        """Get value from environment variable"""
        return os.environ.get(key, default)

    def configure(self, interactive: bool = False):
        """Configure component"""
        raise NotImplementedError