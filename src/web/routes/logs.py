from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from ..app import templates
from ..repository import list_run_logs, get_available_images

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_class=HTMLResponse)
async def show_logs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "logs": list_run_logs(),
            "available_images": get_available_images(),
        },
    )