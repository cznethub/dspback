from functools import lru_cache

from authlib.integrations.starlette_client import OAuth
from pydantic import BaseSettings, HttpUrl
from starlette.config import Config

dotenv_file = ".env"


class Settings(BaseSettings):
    orcid_client_id: str
    orcid_client_secret: str
    orcid_authorize_url: HttpUrl
    orcid_token_url: HttpUrl
    orcid_health_url: HttpUrl

    hydroshare_client_id: str
    hydroshare_client_secret: str
    hydroshare_authorize_url: HttpUrl
    hydroshare_token_url: HttpUrl
    hydroshare_create_url: HttpUrl
    hydroshare_update_url: HttpUrl
    hydroshare_read_url: HttpUrl
    hydroshare_delete_url: HttpUrl
    hydroshare_file_create_url: HttpUrl
    hydroshare_file_delete_url: HttpUrl
    hydroshare_file_read_url: HttpUrl
    hydroshare_view_url: HttpUrl
    hydroshare_folder_create_url: HttpUrl
    hydroshare_folder_read_url: HttpUrl
    hydroshare_folder_delete_url: HttpUrl
    hydroshare_move_or_rename_url: HttpUrl
    hydroshare_health_url: HttpUrl

    zenodo_client_id: str
    zenodo_client_secret: str
    zenodo_authorize_url: HttpUrl
    zenodo_token_url: HttpUrl
    zenodo_create_url: HttpUrl
    zenodo_update_url: HttpUrl
    zenodo_read_url: HttpUrl
    zenodo_delete_url: HttpUrl
    zenodo_file_create_url: HttpUrl
    zenodo_file_delete_url: HttpUrl
    zenodo_file_read_url: HttpUrl
    zenodo_view_url: HttpUrl
    zenodo_health_url: HttpUrl

    earthchem_client_id: str
    earthchem_client_secret: str
    earthchem_authorize_url: HttpUrl
    earthchem_token_url: HttpUrl
    earthchem_create_url: HttpUrl
    earthchem_update_url: HttpUrl
    earthchem_read_url: HttpUrl
    earthchem_delete_url: HttpUrl
    earthchem_file_create_url: HttpUrl
    earthchem_file_delete_url: HttpUrl
    earthchem_file_read_url: HttpUrl
    earthchem_view_url: HttpUrl
    earthchem_health_url: HttpUrl

    gitlab_client_id: str
    gitlab_client_secret: str
    gitlab_authorize_url: HttpUrl
    gitlab_token_url: HttpUrl
    gitlab_create_url: HttpUrl
    gitlab_update_url: HttpUrl
    gitlab_read_url: HttpUrl
    gitlab_delete_url: HttpUrl
    gitlab_file_create_url: HttpUrl
    gitlab_file_delete_url: HttpUrl
    gitlab_file_read_url: HttpUrl
    gitlab_view_url: HttpUrl
    gitlab_health_url: HttpUrl

    database_username: str
    database_password: str
    database_name: str
    database_port: int = 5432
    database_host: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 12 * 60

    session_secret_key: str

    outside_host: str

    @property
    def database_url(self):
        return f'postgresql://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}'

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

oauth.register(
    name='earthchem',
    authorize_url=settings.earthchem_authorize_url,
    token_endpoint=settings.earthchem_token_url,
    access_token_params={
        'grant_type': 'client_credentials',
        'client_id': settings.earthchem_client_id,
        'client_secret': settings.earthchem_client_secret,
    },
)
oauth.register(
    name='gitlab',
    authorize_url=settings.gitlab_authorize_url,
    # client_kwargs={'scope': 'deposit:write deposit:actions', 'response_type': "code"},
    token_endpoint=settings.gitlab_token_url,
    access_token_params={
        'grant_type': 'authorization_code',
        # 'scope': 'deposit:write deposit:actions',
        'client_id': settings.gitlab_client_id,
        'client_secret': settings.gitlab_client_secret,
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
        "view_url": settings.zenodo_view_url,
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
        "folder_create": settings.hydroshare_folder_create_url,
        "folder_read": settings.hydroshare_folder_read_url,
        "folder_delete": settings.hydroshare_folder_read_url,
        "move_or_rename_url": settings.hydroshare_move_or_rename_url,
        "view_url": settings.hydroshare_view_url,
        "schema": "/api/schema/hydroshare/schema.json",
        "uischema": "/api/schema/hydroshare/uischema.json",
        "schema_defaults": "/api/schema/hydroshare/defaults.json",
        "access_token": "/api/access_token/hydroshare",
        "authorize_url": "/api/authorize/hydroshare",
    },
    "earthchem": {
        "create": settings.earthchem_create_url,
        "update": settings.earthchem_update_url,
        "read": settings.earthchem_read_url,
        "delete": settings.earthchem_delete_url,
        "file_create": settings.earthchem_file_create_url,
        "file_delete": settings.earthchem_file_delete_url,
        "file_read": settings.earthchem_file_read_url,
        "view_url": settings.earthchem_view_url,
        "schema": "/api/schema/earthchem/schema.json",
        "uischema": "/api/schema/earthchem/uischema.json",
        "schema_defaults": "/api/schema/earthchem/defaults.json",
        "access_token": "/api/access_token/earthchem",
        "authorize_url": "/api/authorize/earthchem",
    },
    "external": {
        "create": None,
        "update": None,
        "read": None,
        "delete": None,
        "file_create": None,
        "file_delete": None,
        "file_read": None,
        "folder_create": None,
        "view_url": None,
        "schema": "/api/schema/external/schema.json",
        "uischema": "/api/schema/external/uischema.json",
        "schema_defaults": "/api/schema/external/defaults.json",
        "access_token": None,
        "authorize_url": None,
    },
    "gitlab": {
        "create": settings.gitlab_create_url,
        "update": settings.gitlab_update_url,
        "read": settings.gitlab_read_url,
        "delete": settings.gitlab_delete_url,
        "file_create": settings.gitlab_file_create_url,
        "file_delete": settings.gitlab_file_delete_url,
        "file_read": settings.gitlab_file_read_url,
        "view_url": settings.gitlab_view_url,
        "schema": "/api/schema/gitlab/schema.json",
        "uischema": "/api/schema/gitlab/uischema.json",
        "schema_defaults": "/api/schema/gitlab/defaults.json",
        "access_token": "/api/access_token/gitlab",
        "authorize_url": "/api/authorize/gitlab",
    },
}
