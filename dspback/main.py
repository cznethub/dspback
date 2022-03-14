import uvicorn as uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from dspback.config import get_settings
from dspback.database.models import SessionLocal
from dspback.routers import authentication, metadata_class, repository_authorization, submissions

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret_key)

app.mount("/api/schema", StaticFiles(directory="dspback/schemas"), name="schemas")

app.include_router(authentication.router, prefix="/api", tags=["Authentication"])
app.include_router(repository_authorization.router, prefix="/api", tags=["Repository Authorization"])
app.include_router(submissions.router, prefix="/api", tags=["Submissions"])
app.include_router(metadata_class.router, prefix="/api")


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


openapi_schema = get_openapi(
    title="Data Submission Portal API",
    version="1.0",
    description="Standardized interface with validation for managing metadata across repositories",
    routes=app.routes,
)

app.openapi_schema = openapi_schema

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
