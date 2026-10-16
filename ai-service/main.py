"""
ai-service/main.py
Entry point for Vercel / uvicorn to load the FastAPI app from app.main.
"""
from app.main import app

__all__ = ["app"]
