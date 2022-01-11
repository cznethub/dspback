from functools import lru_cache

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from pydantic import BaseSettings, HttpUrl

dotenv_file = ".env"


class Settings(BaseSettings):
    orcid_client_id: str = "APP-YR919NCIR0VINVE7"
    orcid_client_secret: str = "91bc8cb8-ab11-48aa-a28d-4a7f25559ac6"
    orcid_authorize_url: HttpUrl = "https://sandbox.orcid.org/oauth/authorize"
    orcid_token_url: HttpUrl = "https://sandbox.orcid.org/oauth/token"

    hydroshare_client_id: str = "vuzkXtJ0k3qS2aJ49JKGjXC1AtjAoUnbLIBSYh8w"
    hydroshare_client_secret: str = "PcOuBiScWVrp5KeFXegbUYgRsyBqpV9tpFbaHWfugGBEhkVGVKBUJ921Ovf0msu1I5Vuo3usKZAsqL1C" \
                                    "BFgl64pdZlbRkYxkoCnjhD1nl9KfViTVzhgHgbtRyHUwCKV8"
    hydroshare_authorize_url: HttpUrl = "https://beta.hydroshare.org/o/authorize/"
    hydroshare_token_url: HttpUrl = "https://beta.hydroshare.org/o/token/"
    hydroshare_create_url: HttpUrl = "https://beta.hydroshare.org/hsapi/resource/"
    hydroshare_update_url: HttpUrl = "https://beta.hydroshare.org/hsapi2/resource/%s/json/"
    hydroshare_read_url: HttpUrl = "https://beta.hydroshare.org/hsapi2/resource/%s/json/"
    hydroshare_delete_url: HttpUrl = "https://beta.hydroshare.org/hsapi/resource/%s/"
    hydroshare_file_create_url: HttpUrl = "https://beta.hydroshare.org/hsapi/resource/%s/files/"
    hydroshare_file_delete_url: HttpUrl = "https://beta.hydroshare.org/hsapi/resource/%s/files/%s/"
    hydroshare_file_read_url: HttpUrl = "https://beta.hydroshare.org/hsapi/resource/%s/files/"
    hydroshare_file_view_url: HttpUrl = "https://beta.hydroshare.org/resource/%s"

    zenodo_client_id: str = "uebQrVxskClA7ayRmWP2tcQ2m2L8Ade69iwQHkGv"
    zenodo_client_secret: str = "oybPeVuBb4EgVGDIcBbL3OfIc16WbhKZTQbzwnUABt3smuqJVIybZLfBVUlx"
    zenodo_authorize_url: HttpUrl = "https://sandbox.zenodo.org/oauth/authorize"
    zenodo_token_url: HttpUrl = "https://sandbox.zenodo.org/oauth/token"
    zenodo_create_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions"
    zenodo_update_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s"
    zenodo_read_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s"
    zenodo_delete_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s"
    zenodo_file_create_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s/files"
    zenodo_file_delete_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s/files/%s"
    zenodo_file_read_url: HttpUrl = "https://sandbox.zenodo.org/api/deposit/depositions/%s/files"
    zenodo_file_view_url: HttpUrl = "https://sandbox.zenodo.org/deposit/%s"

    database_username: str = "username"
    database_password: str = "password"
    database_name: str = "default_database"
    database_port: int = 5432
    database_host: str = "database"

    @property
    def database_url(self):
        return f'postgresql://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}'

    jwt_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 12 * 60

    session_secret_key: str = "!secret"

    outside_host: str = "localhost"

    class Config:
        env_file = dotenv_file


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
config = Config(dotenv_file)
oauth = OAuth(config)
oauth.register(
    name='orcid',
    authorize_url=settings.orcid_authorize_url,
    token_endpoint=settings.orcid_token_url,
    client_kwargs={'scope': 'openid'},
)

oauth.register(
    name='hydroshare',
    authorize_url=settings.hydroshare_authorize_url,
    token_endpoint=settings.hydroshare_token_url,
)

oauth.register(
    name='zenodo',
    authorize_url=settings.zenodo_authorize_url,
    client_kwargs={'scope': 'deposit:write deposit:actions', 'response_type': "code"},
    token_endpoint=settings.zenodo_token_url,
    access_token_params={
        'grant_type': 'authorization_code',
        'scope': 'deposit:write deposit:actions',
        'client_id': settings.zenodo_client_id,
        'client_secret': settings.zenodo_client_secret,
    },
)

repository_config = {
    "zenodo": {
        "create": settings.zenodo_create_url,
        "update": settings.zenodo_update_url,
        "read": settings.zenodo_read_url,
        "delete": settings.zenodo_delete_url,
        "file_create": settings.zenodo_file_create_url,
        "file_delete": settings.zenodo_file_delete_url,
        "file_read": settings.zenodo_file_read_url,
        "view_url": settings.zenodo_file_view_url,
        "schema": "/api/schema/zenodo/schema.json",
        "uischema": "/api/schema/zenodo/uischema.json",
        "schema_defaults": "/api/schema/zenodo/defaults.json",
        "access_token": "/api/access_token/zenodo",
        "authorize_url": "/api/authorize/zenodo",
    },
    "hydroshare": {
        "create": settings.hydroshare_create_url,
        "update": settings.hydroshare_update_url,
        "read": settings.hydroshare_read_url,
        "delete": settings.hydroshare_delete_url,
        "file_create": settings.hydroshare_file_create_url,
        "file_delete": settings.hydroshare_file_delete_url,
        "file_read": settings.hydroshare_file_read_url,
        "view_url": settings.hydroshare_file_view_url,
        "schema": "/api/schema/hydroshare/schema.json",
        "uischema": "/api/schema/hydroshare/uischema.json",
        "schema_defaults": "/api/schema/hydroshare/defaults.json",
        "access_token": "/api/access_token/hydroshare",
        "authorize_url": "/api/authorize/hydroshare",
    },
}
