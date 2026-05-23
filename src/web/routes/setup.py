from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from ..app import templates
from ..repository import (
    is_first_run,
    set_admin_credentials,
    upsert_config_bulk,
    set_schedule_time_in_db,
    get_all_configs,
    get_or_create_ntfy_topic,
)
from .. import scheduler

router = APIRouter(tags=["Setup"])


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    if not is_first_run():
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        request=request,
        name="setup.html",
        context={
            "values": get_all_configs(),
        },
    )


@router.post("/setup")
async def setup_submit(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    exam_name: str = Form(),
    exam_date_time: str = Form(),
    schedule_time: str = Form(),
    ntfy_enabled: str | None = Form(default=None),
):
    if not is_first_run():
        raise HTTPException(status_code=403, detail="Setup already completed")

    if len(username.strip()) < 3 or len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="setup.html",
            context={
                "values": {
                    "exam_name": exam_name,
                    "exam_date_time": exam_date_time,
                    "schedule_time": schedule_time,
                },
                "error": "Username must be  ≥3 chars and password ≥8 chars.",
            },
            status_code=400,
        )
    try:
        set_schedule_time_in_db(schedule_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    upsert_config_bulk(
        {
            "exam_name": exam_name.strip(),
            "exam_date_time": exam_date_time.strip(),
            "ntfy_enabled": "true" if ntfy_enabled else "false",
        }
    )
    get_or_create_ntfy_topic()
    set_admin_credentials(username=username.strip(), password=password)

    scheduler.apply_schedule_from_db()

    request.session["user"] = username.strip()
    return RedirectResponse("/config", status_code=303)
