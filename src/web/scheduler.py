import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .repository import (
    load_config_from_db,
    create_run_log,
    finalize_run_log,
    get_schedule_time_from_db,
)
from core.job import run_job

JOB_ID = "daily_countdown_job"
SCHEDULER_TZ = os.getenv("TZ", "Asia/Taipei")

_scheduler: BackgroundScheduler | None = None


def _run_scheduled_job():
    config = load_config_from_db()
    log_id = create_run_log()
    result = run_job(config, dry_run=False, run_log_id=log_id)
    finalize_run_log(log_id=log_id, result=result)
    print("[Info] Job result:", result)


def _parse_hh_mm(hh_mm: str) -> tuple[int, int]:
    h, m = hh_mm.split(":")
    return int(h), int(m)


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=SCHEDULER_TZ)
    return _scheduler


def start():
    """Start the scheduler and add the daily job."""
    _scheduler = get_scheduler()
    if not _scheduler.running:
        _scheduler.start()
    apply_schedule_from_db()


def shutdown():
    """Shutdown the scheduler."""
    _scheduler = get_scheduler()
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


def apply_schedule_from_db():
    """Read schedule time from the database and update the scheduled job."""
    hh_mm = get_schedule_time_from_db()
    set_daily_time(hh_mm)
    return hh_mm


def set_daily_time(hh_mm: str):
    h, m = _parse_hh_mm(hh_mm)
    _scheduler = get_scheduler()
    _scheduler.add_job(
        _run_scheduled_job,
        trigger=CronTrigger(hour=h, minute=m),
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def run_now():
    """Run the scheduled job immediately (for testing)."""
    _scheduler = get_scheduler()
    _scheduler.add_job(
        _run_scheduled_job,
        id=f"{JOB_ID}_manual",
        replace_existing=True,
    )
