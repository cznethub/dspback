import uvicorn as uvicorn

from fastapi import FastAPI, Response, Request

from starlette.middleware.sessions import SessionMiddleware

from dspback.config import SESSION_SECRET_KEY
from dspback.database import SessionLocal
from dspback.routers import authentication, repository_authorization, repository_CRUD

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


app.include_router(authentication.router, prefix="/api", tags=["api"])
app.include_router(repository_authorization.router, prefix="/api", tags=["api"])
app.include_router(repository_CRUD.router, prefix="/api", tags=["api"])


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
    uvicorn.run(app, host="0.0.0.0", port=5002, ssl_keyfile="/dspback/dspback/config/example.com+5-key.pem", ssl_certfile="/dspback/dspback/config/example.com+5.pem")
