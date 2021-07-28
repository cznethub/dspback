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
               #access_token_params={'grant_type': 'client_credentials', 'scope': '/read-public',
               #                     'client_id': config.get('ORCID_CLIENT_ID'),
               #                     'client_secret': config.get('ORCID_CLIENT_SECRET')}
               )
oauth.register(name='zenodo',
               authorize_url='https://sandbox.zenodo.org/oauth/authorize',
               client_kwargs={'scope': 'deposit:write deposit:actions', 'response_type': "code"},
               token_endpoint='https://sandbox.zenodo.org/oauth/token',
               access_token_params={'grant_type': 'client_credentials', 'scope': 'deposit:write deposit:actions',
                                    'client_id': config.get('ZENODO_CLIENT_ID'),
                                    'client_secret': config.get('ZENODO_CLIENT_SECRET')})

outside_host = "localhost"

JWT_SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SESSION_SECRET_KEY = "!secret"

repository_config = {
    "zenodo": {
        "host": "sandbox.zenodo.org",
        "create": "/api/deposit/depositions",
        "update": "/api/deposit/depositions/%s",
        "file_add": "/api/deposit/depositions/%s/files",
        "file_delete": "/api/deposit/depositions/%s/files",
        "view": "/api/deposit/depositions/%s",
    }
}