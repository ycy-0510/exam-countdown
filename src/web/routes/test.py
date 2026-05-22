from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..app import templates
from ..repository import (
    load_config_from_db,
    create_run_log,
    finalize_run_log,
    get_run_log,
    get_available_images,
)
from core.job import run_job
from .. import scheduler
from core.ntfy_publisher import test_ntfy as send_test_ntfy
from ..repository import get_or_create_ntfy_topic

router = APIRouter(prefix="/test", tags=["test"])


@router.get("", response_class=HTMLResponse)
async def show_test(
    request: Request,
    log_id: int | None = None,
    message: str | None = None,
):
    log = get_run_log(log_id) if log_id is not None else None
    return templates.TemplateResponse(
        request=request,
        name="test.html",
        context={
            "log": log,
            "available_images": get_available_images() if log else set(),
            "message": message,
        },
    )


@router.post("/dry-run")
async def test_dry_run(request: Request):
    config = load_config_from_db()
    log_id = create_run_log()
    result = run_job(config, dry_run=True, run_log_id=log_id)
    finalize_run_log(log_id=log_id, result=result)
    return RedirectResponse(url=f"/test?log_id={log_id}", status_code=303)


@router.post("/post-now")
async def test_post_now():
    scheduler.run_now()
    return RedirectResponse(
        url="/test?message=Job+scheduled+to+run+immediately", status_code=303
    )


@router.post("/ntfy")
async def test_ntfy_route():
    topic = get_or_create_ntfy_topic()
    ok, summary, detail = send_test_ntfy(topic=topic)
    return {"success": ok, "summary": summary, "detail": detail, "topic": topic}
