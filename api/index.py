"""Vercel Serverless Function entrypoint for Smart Health PHC/CHC app."""
import sys
from pathlib import Path

# Ensure the root project directory is on sys.path for serverless execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app

# Export the FastAPI ASGI app for Vercel Python serverless runtime
__all__ = ["app"]
