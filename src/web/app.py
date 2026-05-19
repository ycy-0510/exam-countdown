from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from .db import init_db
from . import scheduler

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    print("[Info] App started and scheduler running.")
    yield
    scheduler.shutdown()
    print("[Info] App shutting down and scheduler stopped.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return RedirectResponse(url="/config")

from .routes.config import router as config_router
from .routes.logs import router as logs_router
from .routes.test import router as test_router

app.include_router(config_router)
app.include_router(logs_router)
app.include_router(test_router)
