"""
UI server module for serving static files.

This module provides functionality for serving the UI static files.
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from src.api.endpoints import app as api_app

logger = logging.getLogger(__name__)

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Mount static files
api_app.mount("/static", StaticFiles(directory=static_dir), name="static")

@api_app.get("/ui", response_class=HTMLResponse, tags=["UI"])
async def ui_root(request: Request):
    """
    Serve the UI homepage.
    
    Args:
        request (Request): FastAPI request
    
    Returns:
        HTMLResponse: UI homepage
    """
    try:
        # Return the index.html file
        return FileResponse(os.path.join(static_dir, "index.html"))
    except Exception as e:
        logger.error(f"Error serving UI: {e}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")
