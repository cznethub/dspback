import motor
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dspback.config import get_settings
from dspback.pydantic_schemas import Submission, User
from dspback.routers import (
    discovery,
    external,
    submissions,
)

with open('dspback/swagger_plugin/nonce.js', 'r') as f:
    nonce_plugin = f.read()

swagger_ui_parameters = {'plugins': [nonce_plugin]}

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

app.include_router(external.router, prefix="/api")
app.include_router(submissions.router, prefix="/api", tags=["Submissions"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery"])


@app.on_event("startup")
async def startup_db_client():
    app.db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(
        database=app.db[get_settings().mongo_database], document_models=[User, Submission]
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
