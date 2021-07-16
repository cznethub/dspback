import uvicorn as uvicorn

from fastapi import FastAPI

from starlette.middleware.sessions import SessionMiddleware
from oauth_client import app as oauth_client_app
from repos import app as repo_app


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")


app.mount("/api", oauth_client_app)
app.mount("/api", repo_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
