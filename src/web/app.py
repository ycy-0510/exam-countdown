from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from minify_html import minify
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db
from . import scheduler

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"


class MinifyingTemplates(Jinja2Templates):
    def TemplateResponse(self, *args, **kwargs):
        if os.getenv("DEBUG", "false").lower() == "true":
            return super().TemplateResponse(*args, **kwargs)
        response = super().TemplateResponse(*args, **kwargs)
        minified = minify(response.body.decode("utf-8"), minify_css=True, minify_js=True)  # type: ignore
        response.body = minified.encode("utf-8")
        response.headers["Content-Length"] = str(len(response.body))
        return response


templates = MinifyingTemplates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    print("[Info] App started and scheduler running.")
    yield
    scheduler.shutdown()
    print("[Info] App shutting down and scheduler stopped.")


DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
)


SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
)
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is not set")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="session",
    https_only=os.getenv("ALWAYS_HTTPS", "false").lower() == "true",
    same_site="lax",
    max_age=60 * 60 * 24 * 7,
)

STATIC_DIR = WEB_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/config")
    return RedirectResponse("/login")


from fastapi import Depends
from .auth import require_login
from .routes.auth import router as auth_router
from .routes.config import router as config_router
from .routes.logs import router as logs_router
from .routes.test import router as test_router
from .routes.output import router as output_router
from .routes.template import router as template_router
from .routes.stream import router as stream_router

protected = [Depends(require_login)]

app.include_router(auth_router)
app.include_router(config_router, dependencies=protected)
app.include_router(logs_router, dependencies=protected)
app.include_router(test_router, dependencies=protected)
app.include_router(output_router, dependencies=protected)
app.include_router(template_router, dependencies=protected)
app.include_router(stream_router, dependencies=protected)
