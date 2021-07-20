import uvicorn as uvicorn

from fastapi import FastAPI
from fastapi_users.authentication import CookieAuthentication

from starlette.middleware.sessions import SessionMiddleware

from backend.db import database
from routers.users import fastapi_users, SECRET, cookie_authentication
from oauth_client import app as oauth_client_app
from repos import app as repo_app


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")


app.include_router(oauth_client_app, prefix="/api", tags=["api"])
app.include_router(repo_app, prefix="/api", tags=["api"])

# users

app.include_router(
    fastapi_users.get_auth_router(cookie_authentication), prefix="/api/auth/cookie", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(), prefix="/api/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(
        SECRET
    ),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(
        SECRET
    ),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_users_router(), prefix="/api/users", tags=["users"])

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
