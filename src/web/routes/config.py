import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from pydantic import BaseModel
from ..app import templates
from ..repository import (
    get_all_configs,
    upsert_config,
    upsert_config_bulk,
    set_schedule_time_in_db,
    set_platform_enabled,
    get_or_create_ntfy_topic,
    get_ntfy_enabled,
    PLATFORMS,
)
from .. import scheduler
from core.ig_publisher import test_instagram
from core.fb_publisher import test_facebook
from core.discord_publisher import test_discord
from core.image_generator import PALETTE
from core.ntfy_publisher import generate_random_topic, DEFAULT_SERVER as NTFY_SERVER, test_ntfy as send_test_ntfy
import re

router = APIRouter(prefix="/config", tags=["config"])

GENERAL_FIELDS = [
    ("exam_name", "Exam Name", "text"),
    ("exam_date_time", "Exam Date Time", "datetime-local"),
    ("schedule_time", "Schedule Time (HH:MM)", "time"),
]

PLATFORM_FIELDS = {
    "instagram": [
        ("instagram_account_id", "Instagram Account ID", "text"),
        ("instagram_access_token", "Instagram Access Token", "password"),
    ],
    "facebook": [
        ("facebook_page_id", "Facebook Page ID", "text"),
        ("facebook_access_token", "Facebook Access Token", "password"),
    ],
    "discord": [
        ("discord_webhook_url", "Discord Webhook URL", "url"),
    ],
}


@router.get("", response_class=HTMLResponse)
async def show_config(request: Request):
    values = get_all_configs()
    exam_date_time = values.get("exam_date_time")
    if exam_date_time:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                dt = time.strptime(exam_date_time, fmt)
                values["exam_date_time"] = time.strftime("%Y-%m-%dT%H:%M", dt)
                break
            except ValueError:
                continue
    platforms_state = [
        {
            "name": platform.capitalize(),
            "key": platform,
            "enabled": values.get(f"{platform}_enabled", "false") == "true",
            "fields": PLATFORM_FIELDS[platform],
            "configured": all(
                values.get(field[0]) for field in PLATFORM_FIELDS[platform]
            ),
        }
        for platform in PLATFORMS
    ]
    return templates.TemplateResponse(
        request=request,
        name="config.html",
        context={
            "general_fields": GENERAL_FIELDS,
            "platforms": platforms_state,
            "values": values,
            "palette": PALETTE,
            "now": int(time.time()),
            "ntfy": {
                "topic": get_or_create_ntfy_topic(),
                "enabled": get_ntfy_enabled(),
                "server": NTFY_SERVER,
            },
        },
    )


class FieldUpdate(BaseModel):
    key: str
    value: str


@router.post("/field")
async def update_field(payload: FieldUpdate):
    if not payload.value.strip():
        raise HTTPException(status_code=400, detail=f"{payload.key} cannot be empty")
    if payload.key == "schedule_time":
        try:
            set_schedule_time_in_db(payload.value)
            scheduler.apply_schedule_from_db()
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid schedule time format: {e}"
            )
    else:
        upsert_config(payload.key, payload.value)
    return {"ok": True}


class PlatformUpdate(BaseModel):
    fields: dict[str, str]


@router.post("/platform/{platform}")
async def update_platform(platform: str, payload: PlatformUpdate):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}")
    expected_keys = {f[0] for f in PLATFORM_FIELDS[platform]}
    items = {k: v.strip() for k, v in payload.fields.items() if k in expected_keys}
    upsert_config_bulk(items)
    # If any required field is now empty, force-disable to avoid silent skips
    if any(not v for v in items.values()):
        set_platform_enabled(platform, False)
    return {"ok": True}


class PlatformToggle(BaseModel):
    enabled: bool


@router.post("/platform/{platform}/toggle")
async def toggle_platform(platform: str, payload: PlatformToggle):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}")
    if payload.enabled:
        configs = get_all_configs()
        required = [f[0] for f in PLATFORM_FIELDS[platform]]
        missing = [k for k in required if not configs.get(k)]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot enable {platform}: missing {', '.join(missing)}",
            )
    set_platform_enabled(platform, payload.enabled)
    return {"ok": True, "enabled": payload.enabled}


@router.post("/test/{platform}")
async def test_platform(platform: str, payload: PlatformUpdate):
    f = payload.fields
    if platform == "instagram":
        ok, summary, detail = test_instagram(
            f.get("instagram_account_id", ""), f.get("instagram_access_token", "")
        )
    elif platform == "facebook":
        ok, summary, detail = test_facebook(
            f.get("facebook_page_id", ""), f.get("facebook_access_token", "")
        )
    elif platform == "discord":
        ok, summary, detail = test_discord(f.get("discord_webhook_url", ""))
    else:
        raise HTTPException(status_code=404, detail=f"Unknown platform: {platform}")
    return {"success": ok, "summary": summary, "detail": detail}

NTFY_TOPIC_RE = re.compile(r"[A-Za-z0-9_\-]{1,64}")

@router.post("/ntfy/topic")
async def update_ntfy_topic(payload: FieldUpdate):
    topic = payload.value.strip()
    if not NTFY_TOPIC_RE.fullmatch(topic):
        raise HTTPException(
            status_code=400,
            detail="Topic must be 1-64 chars; letters, digits, _ or - only.",
        )
    upsert_config("ntfy_topic",topic)
    return {"ok":True,"topic":topic}

@router.post("/ntfy/regenerate")
async def regenerate_ntfy_topic():
    topic = generate_random_topic()
    return {"ok":True,"topic":topic}

@router.post("/ntfy/toggle")
async def toggle_ntfy(payload: PlatformToggle):
    upsert_config("ntfy_enabled","true" if payload.enabled else "false")
    return {"ok": True, "enabled": payload.enabled}

@router.post("/ntfy/test")
async def test_ntfy_with_topic(payload: FieldUpdate):
    topic = payload.value.strip()
    if not NTFY_TOPIC_RE.fullmatch(topic):
        raise HTTPException(status_code=400, detail="Invalid topic")
    ok, summary, detail = send_test_ntfy(topic=topic)
    return {"success": ok, "summary": summary, "detail": detail}