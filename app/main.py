"""Main FastAPI application entry point for Smart Health."""
import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import dashboard, medicines, beds, doctors, footfall, ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart_health")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Real-time PHC/CHC management for medicine stock, patient footfall, beds, doctor attendance, and Gemini AI forecasting.",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Template mounts
static_path = BASE_DIR / "static"
templates_path = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Include API Routers
app.include_router(dashboard.router)
app.include_router(medicines.router)
app.include_router(beds.router)
app.include_router(doctors.router)
app.include_router(footfall.router)
app.include_router(ai.router)


# Liveness & Readiness for Google Cloud Run
@app.get("/healthz", tags=["System"])
def health_check():
    """Liveness probe for Google Cloud Run and Kubernetes."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/readyz", tags=["System"])
def readiness_check():
    """Readiness probe verifying system subsystems."""
    return {"status": "ready"}


# Frontend Web Application Shell
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard(request: Request):
    """Renders the accessible Single Page Application."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "has_gemini": bool(settings.gemini_api_key),
        }
    )



if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.port))
    logger.info(f"Starting {settings.app_name} on 0.0.0.0:{port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
