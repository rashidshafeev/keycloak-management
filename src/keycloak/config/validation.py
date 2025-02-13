"""
Validation utilities for Keycloak configuration.
"""

class ValidationError(Exception):
    """Raised when configuration validation fails."""
    def __init__(self, message: str, path: str = None):
        self.message = message
        self.path = path
        super().__init__(f"{message} (at {path})" if path else message)


def validate_required(value: any, field_name: str, path: str = None) -> None:
    """Validate that a required field is present and not None."""
    if value is None:
        raise ValidationError(f"Required field '{field_name}' is missing", path)


def validate_string(value: str, field_name: str, path: str = None) -> None:
    """Validate that a field is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Field '{field_name}' must be a non-empty string", path)


def validate_boolean(value: bool, field_name: str, path: str = None) -> None:
    """Validate that a field is a boolean."""
    if not isinstance(value, bool):
        raise ValidationError(f"Field '{field_name}' must be a boolean", path)


def validate_list(value: list, field_name: str, path: str = None) -> None:
    """Validate that a field is a list."""
    if not isinstance(value, list):
        raise ValidationError(f"Field '{field_name}' must be a list", path)


def validate_dict(value: dict, field_name: str, path: str = None) -> None:
    """Validate that a field is a dictionary."""
    if not isinstance(value, dict):
        raise ValidationError(f"Field '{field_name}' must be a dictionary", path)
