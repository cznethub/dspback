import random
import string
from functools import lru_cache

from authlib.integrations.starlette_client import OAuth
from pydantic import BaseSettings, HttpUrl
from starlette.config import Config

dotenv_file = ".env"


class Settings(BaseSettings):
    keycloak_host: str = "https://auth.cuahsi.io"
    keycloak_realm: str = "HydroShare"
    keycloak_client_id: str = "local_iguide_api"
    keycloak_client_secret: str = "AyPQBiRP1FAJ7bU8rIUopgtFExc6ySkR"
    keycloak_app_uri: str = "https://localhost/api"
    keycloak_redirect_uri: str = "https://localhost/api"

    mongo_username: str
    mongo_password: str
    mongo_host: str
    mongo_database: str
    mongo_protocol: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 12 * 60
    access_token_expiration_buffer_seconds: int = 30 * 60

    session_secret_key: str# = "".join(random.choice(string.ascii_letters) for _ in range(16))

    outside_host: str

    @property
    def local_development(self):
        return self.outside_host == "localhost"

    @property
    def mongo_url(self):
        return f"{self.mongo_protocol}://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}/?retryWrites=true&w=majority"

    class Config:
        env_file = dotenv_file


@lru_cache()
def get_settings():
    return Settings()
