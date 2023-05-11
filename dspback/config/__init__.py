from functools import lru_cache

from authlib.integrations.starlette_client import OAuth
from pydantic import BaseSettings, HttpUrl
from starlette.config import Config

dotenv_file = ".env"


class Settings(BaseSettings):
    keycloak_client_id: str
    keycloak_client_secret: str
    keycloak_authorize_url: HttpUrl
    keycloak_token_url: HttpUrl
    keycloak_health_url: HttpUrl

    mongo_username: str
    mongo_password: str
    mongo_host: str
    mongo_database: str
    mongo_protocol: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 12 * 60
    access_token_expiration_buffer_seconds: int = 30 * 60

    session_secret_key: str

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


settings = get_settings()
config = Config(dotenv_file)
oauth = OAuth(config)
oauth.register(
    name='keycloak',
    authorize_url=settings.keycloak_authorize_url,
    token_endpoint=settings.keycloak_token_url,
    client_kwargs={'scope': 'openid profile email'},
)
