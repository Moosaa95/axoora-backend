import uuid
from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = 'Common Shared Modules'

    def ready(self):
        """
        Safeguard SQLite UUID conversion against integer or malformed values.
        Prevents AttributeError: 'int' object has no attribute 'replace' in uuid.py line 175.
        """
        try:
            from django.db.backends.sqlite3.operations import DatabaseOperations

            def safe_convert_uuidfield_value(self, value, expression, connection):
                if value is None:
                    return None
                if isinstance(value, uuid.UUID):
                    return value
                if isinstance(value, int):
                    return uuid.UUID(int=value)
                try:
                    return uuid.UUID(str(value))
                except (ValueError, AttributeError, TypeError):
                    return None

            DatabaseOperations.convert_uuidfield_value = safe_convert_uuidfield_value
        except Exception:
            pass
