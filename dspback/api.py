import motor
from beanie import init_beanie
from fastapi import FastAPI, status
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse

from dspback.config import get_settings
from dspback.dependencies import RepositoryException
from dspback.pydantic_schemas import RepositoryToken, Submission, User
from dspback.routers import (
    authentication,
    discovery,
    earthchem,
    external,
    hydroshare,
    repository_authorization,
    submissions,
    zenodo,
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery"])


@app.exception_handler(RepositoryException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(f"Repository exception response[{str(exc.detail)}]", status_code=exc.status_code)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return PlainTextResponse(f"Request data validation errors: {str(exc)}", status_code=status.HTTP_400_BAD_REQUEST)


@app.on_event("startup")
async def startup_db_client():
    app.db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(
        database=app.db[get_settings().mongo_database], document_models=[User, Submission, RepositoryToken]
    )


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
