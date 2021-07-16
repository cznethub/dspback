import time

from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse, JSONResponse
from db import db


app = FastAPI()

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

def _access_token(request: Request, repository: str):
    orcid = request.session.get('orcid')
    expires_at = db[orcid][repository]['expires_at']
    if expires_at < time.time():
        pass
    return db[orcid][repository]['access_token']


@app.route('/')
def home(request: Request):
    orcid = request.session.get('orcid')
    if orcid:
        if orcid in db:
            return JSONResponse(content={orcid: db[orcid]})
        return JSONResponse(content={"status": f"{orcid} not recognized"})
    return JSONResponse(content={"status": "Not logged in"})

@app.get("/create/{repository}/")
def create_url(request: Request, repository: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["create"]
    access_token = _access_token(request, repository)
    return f"https://{host}{path}?access_token={access_token}"


@app.get("/update/{repository}/{pid}/")
def update_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["update"] % pid
    access_token = _access_token(request, repository)
    return f"https://{host}{path}?access_token={access_token}"


@app.get("/view/{repository}/{pid}/")
def view_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["view"] % pid
    access_token = _access_token(request, repository)
    return f"https://{host}{path}?access_token={access_token}"


@app.get("/files/{repository}/{pid}/")
def update_files_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["files"] % pid
    access_token = _access_token(request, repository)
    return f"https://{host}{path}?access_token={access_token}"
