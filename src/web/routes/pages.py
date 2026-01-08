from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Configurar templates (debe coincidir con la config en app.py, o inyectarse)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page principal."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    """Página de Preguntas Frecuentes."""
    return templates.TemplateResponse("faq.html", {"request": request})

@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """Términos y Condiciones."""
    return templates.TemplateResponse("terms.html", {"request": request})

@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Política de Privacidad."""
    return templates.TemplateResponse("privacy.html", {"request": request})

