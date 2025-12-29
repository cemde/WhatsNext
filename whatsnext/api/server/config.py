from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Database settings (defaults allow module import without .env for testing)
    database_hostname: str = "localhost"
    database_port: int = 5432
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_name: str = "whatsnext"

    # API key authentication (optional - if not set, authentication is disabled)
    api_keys: Optional[str] = None  # Comma-separated list of valid API keys

    # CORS settings
    cors_origins: str = "*"  # Comma-separated list of allowed origins, or "*" for all
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    # Rate limiting (requests per minute, 0 = disabled)
    rate_limit_per_minute: int = 0

    def get_api_keys(self) -> List[str]:
        """Return list of valid API keys, or empty list if auth is disabled."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    def get_cors_origins(self) -> List[str]:
        """Return list of allowed CORS origins."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


class DBSettings:
    def __init__(self, settings: Settings):
        self.hostname = settings.database_hostname
        self.port = settings.database_port
        self.user = settings.database_user
        self.password = settings.database_password
        self.database = settings.database_name


settings = Settings()

db = DBSettings(settings)
