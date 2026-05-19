from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..app import templates
from ..repository import load_config_from_db, create_run_log, finalize_run_log
from core.job import run_job
from .. import scheduler

router = APIRouter(prefix="/test", tags=["test"])


@router.get("", response_class=HTMLResponse)
async def show_test(request: Request, result: str | None = None):
    return templates.TemplateResponse(
        request=request, name="test.html", context={"result": result}
    )


@router.post("/dry-run")
async def test_dry_run(request: Request):
    config = load_config_from_db()
    log_id = create_run_log()
    result = run_job(config, dry_run=True, run_log_id=log_id)
    finalize_run_log(log_id=log_id, result=result)
    return RedirectResponse(url=f"/test?result={result}", status_code=303)


@router.post("/post-now")
async def test_post_now():
    scheduler.run_now()
    return RedirectResponse(
        url=f"/test?result=Job scheduled to run immediately", status_code=303
    )
