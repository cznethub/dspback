from fastapi import Request, APIRouter
from starlette.responses import HTMLResponse

from backend.config import repository_config
from backend.dependencies import access_token

router = APIRouter()


@router.get("/create/{repository}/")
def create_url(request: Request, repository: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["create"]
    token = access_token(request, repository)
    return f"https://{host}{path}?access_token={token}"


@router.get("/update/{repository}/{pid}/")
def update_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["update"] % pid
    token = access_token(request, repository)
    return f"https://{host}{path}?access_token={token}"


@router.get("/view/{repository}/{pid}/")
def view_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["view"] % pid
    token = access_token(request, repository)
    return f"https://{host}{path}?access_token={token}"


@router.get("/files/{repository}/{pid}/")
def update_files_url(request: Request, repository: str, pid: str):
    if repository not in repository_config:
        raise HTMLResponse(f"schema {repository} not recognized", status_code=404)
    host = repository_config[repository]["host"]
    path = repository_config[repository]["files"] % pid
    token = access_token(request, repository)
    return f"https://{host}{path}?access_token={token}"
