from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")

from src.web.i18n import get_translation

def get_locale(request: Request):
    return request.cookies.get("lang", "es")

def t_helper(request):
    lang = get_locale(request)
    return lambda key: get_translation(lang, key)

templates.env.globals['t'] = t_helper
templates.env.globals['current_lang'] = get_locale

@router.get("/set_language/{lang}")
async def set_language(lang: str, response: Response):
    if lang not in ["es", "en"]:
        lang = "es"
    # Redirigir a la home por ahora
    redirect_url = "/"
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(key="lang", value=lang)
    return response

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/faq")
async def faq(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})

@router.get("/terms")
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@router.get("/privacy")
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})
