from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path
from ..app import templates
from ..repository import list_run_logs

router = APIRouter(prefix="/logs", tags=["logs"])

OUTPUT_DIR = (Path(__file__).resolve().parent.parent.parent / "output").resolve()

@router.get("", response_class=HTMLResponse)
async def show_logs(request: Request):
    logs = list_run_logs()
    available_images = {f.name for f in OUTPUT_DIR.glob("*.jpg")}

    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "logs": logs,
            "available_images": available_images,
        }
    )