import uvicorn as uvicorn

from fastapi import FastAPI
from fastapi_users.authentication import CookieAuthentication

from starlette.middleware.sessions import SessionMiddleware

from backend import fastapi_users
from backend.database import database
from oauth_client import app as oauth_client_app, orcid_client
from repos import app as repo_app

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")


app.include_router(oauth_client_app, prefix="/api", tags=["api"])
app.include_router(repo_app, prefix="/api", tags=["api"])

# users

SECRET = "SECRET"
cookie_authentication = CookieAuthentication(
    secret=SECRET, lifetime_seconds=3600
)

app.include_router(
    fastapi_users.get_auth_router(cookie_authentication), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(), prefix="/auth", tags=["auth"]
)
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])


google_oauth_router = fastapi_users.get_oauth_router(
    orcid_client, SECRET
)
app.include_router(google_oauth_router, prefix="/auth/orcid", tags=["auth"])

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()


@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002, ssl_keyfile="config/example.com+5-key.pem", ssl_certfile="config/example.com+5.pem")
