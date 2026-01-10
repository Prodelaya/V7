from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")

# We need to re-attach globals because 'pages.py' creates its own templates instance?
# Actually, better to import the main 'templates' from app if possible, or re-define globals here?
# Circular import risk. Let's just rely on the fact that we modify the env in app.py BEFORE usage.
# But 'templates' object is instantiated here separately.
# FIX: In FastAPI, usually better to perform injection in main app or have a shared module.
# For simplicity, let's just re-inject the globals here or assume app.py does it globally if we shared the instance.

# To avoid circular imports, let's just redefine the injection logic or import from a shared config.
# BUT, since I can't easily refactor everything to shared config now without checking files...
# I will modify app.py to pass the templates instance TO the router or mount it.
# Wait, 'pages.py' instantiates Jinja2Templates again. This is bad. It should share it.

# Let's fix this file to NOT instantiate templates again if possible, OR re-apply globals.
# Simpler approach: Import the helper functions from i18n and apply them.

from src.web.i18n import get_translation

def get_locale(request: Request):
    return request.cookies.get("lang", "es")

# Minimal local helper to avoid circular dependency with app.py's t()
def t_helper(request):
    lang = get_locale(request)
    return lambda key: get_translation(lang, key)

templates.env.globals['t'] = t_helper
templates.env.globals['current_lang'] = get_locale

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
