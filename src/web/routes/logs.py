from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from ..app import templates
from ..repository import list_run_logs

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("", response_class=HTMLResponse)
async def show_logs(request: Request):
    logs = list_run_logs()
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "logs": logs,
        }
    )