from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from sqlalchemy import select

from .db import SessionLocal
from .models import Config, RunLog
from core.job import JobResult, JobConfig
from core.ntfy_publisher import generate_random_topic

PLATFORMS = ("instagram", "facebook", "discord")

OUTPUT_DIR = (Path(__file__).resolve().parent.parent / "output").resolve()


def get_available_images() -> set[str]:
    """Return the filenames of currently available countdown images on disk."""
    if not OUTPUT_DIR.exists():
        return set()
    return {p.name for p in OUTPUT_DIR.glob("*.jpg")}


def get_all_configs() -> dict[str, str]:
    """Fetch all configuration key-value pairs from the database."""
    with SessionLocal() as session:
        rows = session.execute(select(Config)).scalars().all()
        return {row.key: row.value for row in rows}


def upsert_config(key: str, value: str) -> None:
    """Update or insert a configuration key-value pair in the database."""
    with SessionLocal() as session:
        row = session.get(Config, key)
        if row:
            row.value = value
        else:
            row = Config(key=key, value=value)
            session.add(row)
        session.commit()


def upsert_config_bulk(items: dict[str, str]) -> None:
    with SessionLocal() as session:
        for key, value in items.items():
            row = session.get(Config, key)
            if row:
                row.value = value
            else:
                row = Config(key=key, value=value)
                session.add(row)
        session.commit()


def get_platform_enabled(platform: str) -> bool:
    return get_all_configs().get(f"{platform}_enabled", "false") == "true"


def set_platform_enabled(platform: str, enabled: bool) -> None:
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform}")
    upsert_config(f"{platform}_enabled", "true" if enabled else "false")


def load_config_from_db() -> JobConfig:
    """Load configuration from the database and return a JobConfig object."""
    configs = get_all_configs()
    return JobConfig(
        exam_date_time=configs.get("exam_date_time", "2030-07-01"),
        exam_name=configs.get("exam_name", "Example Exam"),
        instagram_access_token=configs.get("instagram_access_token") or None,
        instagram_account_id=configs.get("instagram_account_id") or None,
        instagram_enabled=configs.get("instagram_enabled", "false") == "true",
        facebook_access_token=configs.get("facebook_access_token") or None,
        facebook_page_id=configs.get("facebook_page_id") or None,
        facebook_enabled=configs.get("facebook_enabled", "false") == "true",
        discord_webhook_url=configs.get("discord_webhook_url") or None,
        discord_enabled=configs.get("discord_enabled", "false") == "true",
    )


def get_schedule_time_from_db() -> str:
    """Load the scheduled time for the job from the database."""
    configs = get_all_configs()
    return configs.get("schedule_time", "07:00")


def set_schedule_time_in_db(hh_mm: str) -> None:
    """Set the scheduled time for the job in the database."""
    try:
        h, m = hh_mm.split(":")
        assert 0 <= int(h) < 24 and 0 <= int(m) < 60
    except (ValueError, AssertionError):
        raise ValueError("Invalid time format. Expected HH:MM in 24-hour format.")
    upsert_config("schedule_time", hh_mm)


def create_run_log() -> int:
    """Create a new run log entry and return its ID."""
    with SessionLocal() as session:
        log = RunLog(started_at=datetime.now(timezone.utc))
        session.add(log)
        session.commit()
        session.refresh(log)
        return log.id


def finalize_run_log(log_id: int, result: JobResult) -> None:
    """Update the run log entry with the job result."""
    with SessionLocal() as session:
        log = session.get(RunLog, log_id)
        if not log:
            return
        log.finished_at = datetime.now(timezone.utc)
        log.success = result["success"]
        log.days_left = result["days_left"]
        log.image_path = result["image_path"]
        log.ig_status = result["ig_status"]
        log.fb_status = result["fb_status"]
        log.discord_status = result["discord_status"]
        log.error = result.get("error")
        session.commit()


def get_run_log(log_id: int) -> RunLog | None:
    """Fetch a single run log by its ID."""
    with SessionLocal() as session:
        return session.get(RunLog, log_id)


def list_run_logs(limit: int = 50) -> list[RunLog]:
    """Fetch a list of recent run logs from the database."""
    with SessionLocal() as session:
        logs = (
            session.execute(
                select(RunLog).order_by(RunLog.started_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return list(logs)


def get_or_create_ntfy_topic() -> str:
    """Return current ntfy topic; if missing, generate and persist a random one."""
    configs = get_all_configs()
    topic = configs.get("ntfy_topic")
    if not topic:
        topic = generate_random_topic()
        upsert_config("ntfy_topic", topic)
    return topic


def get_ntfy_enabled() -> bool:
    return get_all_configs().get("ntfy_enabled", "true") == "true"
