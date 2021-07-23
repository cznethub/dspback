import uvicorn as uvicorn

from fastapi import FastAPI, Response, Request

from starlette.middleware.sessions import SessionMiddleware

from backend.database import SessionLocal
from oauth_client import app as oauth_client_app
from repos import app as repo_app

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")


app.include_router(oauth_client_app, prefix="/api", tags=["api"])
app.include_router(repo_app, prefix="/api", tags=["api"])


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002, ssl_keyfile="config/example.com+5-key.pem", ssl_certfile="config/example.com+5.pem")
