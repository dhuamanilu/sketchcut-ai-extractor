from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Important: This initializes the environment and AI on startup
import app.core.config 
from app.api.endpoints import router as api_router

app = FastAPI(title="SCT Extractor API MVC")

# Setup Jinja2 for serving the frontend
# Note: Since main.py is now inside app/, we point to the outer templates dir or move templates.
# We will assume templates stays at root level /api/templates for backward compatibility for now.
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Mount the business logic routes under /api
app.include_router(api_router, prefix="/api")

# To run the server now: uvicorn app.main:app --reload
