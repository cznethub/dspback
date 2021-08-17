from starlette.config import Config
from authlib.integrations.starlette_client import OAuth

config_path = "/dspback/dspback/config/.env"


config = Config(config_path)

oauth = OAuth(config)
oauth.register(name='hydroshare',
               authorize_url="https://www.hydroshare.org/o/authorize/",
               token_endpoint="https://www.hydroshare.org/o/token/")
oauth.register(name='orcid',
               authorize_url='https://sandbox.orcid.org/oauth/authorize',
               token_endpoint='https://sandbox.orcid.org/oauth/token',
               client_kwargs={'scope': 'openid'},
               )

oauth.register(name='earthchem',
               authorize_url='https://orcid.org/oauth/authorize',
               token_endpoint='https://orcid.org/oauth/token',
               client_kwargs={'scope': 'openid'}
               )
oauth.register(name='zenodo',
               authorize_url='https://sandbox.zenodo.org/oauth/authorize',
               client_kwargs={'scope': 'deposit:write deposit:actions', 'response_type': "code"},
               token_endpoint='https://sandbox.zenodo.org/oauth/token',
               access_token_params={'grant_type': 'client_credentials', 'scope': 'deposit:write deposit:actions',
                                    'client_id': config.get('ZENODO_CLIENT_ID'),
                                    'client_secret': config.get('ZENODO_CLIENT_SECRET')})

OUTSIDE_HOST = config.get("OUTSIDE_HOST")

JWT_SECRET_KEY = config.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 12*60

SESSION_SECRET_KEY = config.get("SESSION_SECRET_KEY")

DATABASE_USERNAME = config.get("POSTGRES_USER")
DATABASE_PASSWORD = config.get("POSTGRES_PASSWORD")
DATABASE_PORT = "5432"
DATABASE_NAME = config.get("POSTGRES_DB")
DATABASE_HOST = "database"

DATABASE_URL = f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'

repository_config = {
    "zenodo": {
        "host": "sandbox.zenodo.org",
        "create": "/api/deposit/depositions",
        "update": "/api/deposit/depositions/%s",
        "file_create": "/api/deposit/depositions/%s/files",
        "file_delete": "/api/deposit/depositions/%s/files",
        "read": "/api/deposit/depositions/%s",
    }
}