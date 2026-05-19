from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from ..app import templates
from ..repository import get_all_configs, upsert_config_bulk, set_schedule_time_in_db
from .. import scheduler

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_FIELDS = [
    ("exam_name", "Exam Name", "text"),
    ("exam_date_time", "Exam Date Time", "text"),
    ("schedule_time", "Daily Post Time (HH:MM)", "text"),
    ("instagram_account_id", "IG Account ID", "text"),
    ("instagram_access_token", "IG Access Token", "password"),
    ("facebook_page_id", "Facebook Page ID", "text"),
    ("facebook_access_token", "Facebook Access Token", "password"),
    ("discord_webhook_url", "Discord Webhook URL", "text"),
]


@router.get("", response_class=HTMLResponse)
async def show_config(request: Request, message: str | None = None):
    values = get_all_configs()
    return templates.TemplateResponse(
        request=request,
        name="config.html",
        context={
            "fields": CONFIG_FIELDS,
            "values": values,
            "message": message,
        },
    )

@router.post("")
async def save_config(request: Request):
    form = await request.form()
    items = {key: str(form.get(key,"")) for key, _ ,_ in CONFIG_FIELDS}

    try:
        set_schedule_time_in_db(items["schedule_time"])
    except ValueError as e:
        return RedirectResponse(url=f"/config?message=Invalid schedule time format: {e}", status_code=303)
    
    upsert_config_bulk(items)
    scheduler.apply_schedule_from_db()
    return RedirectResponse(url="/config?message=Configuration saved successfully", status_code=303)


