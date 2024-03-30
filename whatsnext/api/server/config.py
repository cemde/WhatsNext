from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_user: str
    database_password: str
    database_name: str

    class Config:
        env_file = ".env"


class DBSettings:
    def __init__(self, settings: Settings):
        self.hostname = settings.database_hostname
        self.port = settings.database_port
        self.user = settings.database_user
        self.password = settings.database_password
        self.database = settings.database_name


settings = Settings()

db = DBSettings(settings)
