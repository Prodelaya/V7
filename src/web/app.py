from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn

from src.web.routes import pages

# Configuración básica
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Retador v2.0",
    description="Sistema profesional de Value Betting",
    version="2.0.0",
    docs_url=None,  # Desactivar docs en prod por seguridad/privacidad
    redoc_url=None
)

# Montar archivos estáticos (CSS, JS, Imágenes)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Configurar Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Incluir routers
app.include_router(pages.router)

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)
