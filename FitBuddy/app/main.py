import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import init_db
from .routes import router

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Resolve static directory (app/static or root static)
static_dir = BASE_DIR / "static" if (BASE_DIR / "static").exists() else ROOT_DIR / "static"

# Resolve templates directory (app/templates or root templates)
template_dir = BASE_DIR / "templates" if (BASE_DIR / "templates").exists() else ROOT_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="Personalized 7-day workout plans, nutrition tips, and feedback-based plan updates using Google Gemini AI.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(template_dir))

# Include core application routes
app.include_router(router)
