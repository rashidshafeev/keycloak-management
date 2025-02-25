"""
Theme configuration for Keycloak.
"""

from pathlib import Path
from .base import KeycloakConfigStep
from .validation import ValidationError


class ThemeConfigStep(KeycloakConfigStep):
    """Handles theme configuration for Keycloak.
    
    This step manages theme settings, including:
    - Custom theme deployment
    - Theme configuration
    - Default theme selection
    """
    
    def _validate_impl(self, config: dict) -> None:
        """Validate theme configuration."""
        themes = config.get('themes', {})
        if not isinstance(themes, dict):
            raise ValidationError("'themes' must be a dictionary", "themes")
        
        for theme_name, theme_config in themes.items():
            if not isinstance(theme_config, dict):
                raise ValidationError(f"Theme '{theme_name}' configuration must be a dictionary", f"themes.{theme_name}")
            
            theme_path = theme_config.get('path')
            if theme_path and not Path(theme_path).exists():
                raise ValidationError(f"Theme path '{theme_path}' does not exist", f"themes.{theme_name}.path")
    
    def _execute_impl(self, config: dict) -> None:
        """Apply theme configuration."""
        themes = config.get('themes', {})
        
        for theme_name, theme_config in themes.items():
            # Deploy custom theme if path is provided
            theme_path = theme_config.get('path')
            if theme_path:
                self._deploy_theme(theme_name, Path(theme_path))
            
            # Set theme as default if specified
            if theme_config.get('default', False):
                self.run_kcadm_command('update', 'realms/master',
                                     '-s', f'loginTheme={theme_name}',
                                     '-s', f'accountTheme={theme_name}',
                                     '-s', f'adminTheme={theme_name}',
                                     '-s', f'emailTheme={theme_name}')
    
    def _rollback_impl(self) -> None:
        """Rollback theme configuration changes."""
        # Reset to default themes
        self.run_kcadm_command('update', 'realms/master',
                             '-s', 'loginTheme=keycloak',
                             '-s', 'accountTheme=keycloak',
                             '-s', 'adminTheme=keycloak',
                             '-s', 'emailTheme=keycloak')
    
    def _deploy_theme(self, theme_name: str, theme_path: Path) -> None:
        """Deploy a custom theme to Keycloak."""
        target_dir = Path('/opt/keycloak/themes') / theme_name
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        
        # Copy theme files
        self.run_kcadm_command('cp', '-r', str(theme_path), str(target_dir))
