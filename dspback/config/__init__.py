from functools import lru_cache

from pydantic import BaseSettings

dotenv_file = ".env"


class Settings(BaseSettings):
    keycloak_issuer: str = "https://auth.cuahsi.io/realms/HydroShare"
    keycloak_client_id: str

    mongo_username: str
    mongo_password: str
    mongo_host: str
    mongo_database: str
    mongo_protocol: str

    session_secret_key: str

    local_development: bool = True

    @property
    def mongo_url(self):
        return f"{self.mongo_protocol}://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}/?retryWrites=true&w=majority"

    class Config:
        env_file = dotenv_file


@lru_cache()
def get_settings():
    return Settings()
