import motor
import uvicorn as uvicorn
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse

from dspback.config import get_settings
from dspback.dependencies import RepositoryException
from dspback.pydantic_schemas import RepositoryToken, Submission, User
from dspback.routers import (
    authentication,
    earthchem,
    external,
    hydroshare,
    repository_authorization,
    submissions,
    zenodo,
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret_key)

app.mount("/api/schema", StaticFiles(directory="dspback/schemas"), name="schemas")

app.include_router(authentication.router, prefix="/api", tags=["Authentication"], include_in_schema=False)
app.include_router(
    repository_authorization.router, prefix="/api", tags=["Repository Authorization"], include_in_schema=False
)
app.include_router(hydroshare.router, prefix="/api")
app.include_router(zenodo.router, prefix="/api")
app.include_router(earthchem.router, prefix="/api")
app.include_router(external.router, prefix="/api")
app.include_router(submissions.router, prefix="/api", tags=["Submissions"])


@app.exception_handler(RepositoryException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(f"Repository exception response[{str(exc.detail)}]", status_code=exc.status_code)


@app.on_event("startup")
async def startup_db_client():
    app.db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().db_url)
    await init_beanie(database=app.db[get_settings().db_name], document_models=[User, Submission, RepositoryToken])


@app.on_event("shutdown")
async def shutdown_db_client():
    app.db.close()


openapi_schema = get_openapi(
    title="Data Submission Portal API",
    version="1.0",
    description="Standardized interface with validation for managing metadata across repositories",
    routes=app.routes,
)
openapi_schema["info"]["contact"] = {
    "name": "Learn more about this API",
    "url": "https://github.com/cznethub/dspback",
    "email": "sblack@cuahsi.org",
}


app.openapi_schema = openapi_schema

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
