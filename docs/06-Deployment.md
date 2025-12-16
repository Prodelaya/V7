# 🚀 Guía de Despliegue y Desarrollo - Retador v2.0

## 📋 Resumen de Entornos

| Entorno        | Sistema        | Redis          | Uso                                |
| -------------- | -------------- | -------------- | ---------------------------------- |
| **Desarrollo** | Windows + WSL  | Docker o local | Desarrollo diario, tests unitarios |
| **Tests**      | Docker         | Container      | Tests de integración               |
| **Producción** | bmax90 (Linux) | Container      | Servicio en producción             |

---

## 🛠️ Estructura de Archivos de Configuración

```
RetadorV7/
├── .env                    # ❌ Gitignored - Config local actual
├── .env.example            # ✅ Template con valores por defecto
├── .env.docker             # ✅ Config específica para Docker
├── pyproject.toml          # Dependencias y metadata del proyecto
├── requirements.txt        # Generado desde pyproject.toml
├── Dockerfile              # Imagen de producción (multi-stage)
├── docker-compose.yml      # Stack de producción
├── docker-compose.dev.yml  # Override para desarrollo
└── .dockerignore           # Optimiza build context
```

---

## ⚙️ Archivos de Entorno (.env)

### ¿Por qué separar `.env` y `.env.docker`?

| Variable     | Local (`.env`) | Docker (`.env.docker`)        |
| ------------ | -------------- | ----------------------------- |
| `REDIS_HOST` | `localhost`    | `redis` (nombre del servicio) |
| Otros        | Igual          | Igual                         |

> **Recomendación**: Usa `.env.docker` para Docker y `.env` para desarrollo local sin Docker.

### Crear archivos de entorno

```bash
# Copiar template
cp .env.example .env
cp .env.example .env.docker

# Editar .env.docker - cambiar solo Redis
sed -i 's/REDIS_HOST=localhost/REDIS_HOST=redis/' .env.docker
```

### Variables críticas a configurar

```bash
# .env / .env.docker
API_TOKEN=tu_token_real_aqui          # ⚠️ OBLIGATORIO
TELEGRAM_BOT_TOKENS=bot1,bot2,bot3    # ⚠️ OBLIGATORIO (5 tokens)
TELEGRAM_LOG_CHANNEL=-100xxxxxxxxxx   # Canal de logs
```

---

## 🐍 Desarrollo Local (Windows + WSL)

### 1. Setup inicial

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Linux/WSL)
source .venv/bin/activate

# Instalar proyecto en modo editable + deps dev
pip install -e ".[dev]"
```

### 2. Ejecutar tests unitarios

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Solo tests unitarios (sin Redis)
pytest tests/unit/
```

### 3. Ejecutar la aplicación localmente

```bash
# Requiere Redis corriendo localmente o en Docker
python -m scripts.run
```

### 4. Linting y formateo

```bash
# Formatear código
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

---

## 🐳 Docker - Desarrollo

### Levantar stack de desarrollo

```bash
# Usa .env.docker automáticamente
docker-compose --env-file .env.docker \
  -f docker-compose.yml \
  -f docker-compose.dev.yml up
```

### Características del modo desarrollo

- **Hot-reload**: Código montado como volumen
- **Redis expuesto**: Puerto 6379 accesible para debugging
- **Logs en tiempo real**: Sin detach

### Comandos útiles

```bash
# Ver logs de la app
docker-compose logs -f retador

# Conectar a Redis para debugging
docker-compose exec redis redis-cli

# Ejecutar comando dentro del contenedor
docker-compose exec retador python -c "print('hello')"

# Reconstruir después de cambios en Dockerfile
docker-compose build --no-cache
```

---

## 🧪 Docker - Tests de Integración

### Ejecutar tests con Redis real

```bash
# Levantar solo Redis
docker-compose up -d redis

# Ejecutar tests de integración
pytest tests/integration/ -v

# Limpiar
docker-compose down
```

### Con Testcontainers (recomendado)

```python
# tests/integration/conftest.py
import pytest
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis_url():
    with RedisContainer() as redis:
        yield redis.get_connection_url()
```

```bash
# Instalar testcontainers
pip install testcontainers[redis]

# Ejecutar - Docker crea/destruye Redis automáticamente
pytest tests/integration/
```

---

## 🏭 Producción - Servidor bmax90

### 1. Preparar el servidor

```bash
# SSH al servidor
ssh usuario@bmax90

# Clonar repositorio
git clone <repo-url> /opt/retador
cd /opt/retador

# Crear archivo de entorno de producción
cp .env.example .env.docker
nano .env.docker  # Configurar valores reales
```

### 2. Configurar .env.docker para producción

```bash
# .env.docker (producción)
API_TOKEN=token_real_de_produccion
TELEGRAM_BOT_TOKENS=bot1_real,bot2_real,bot3_real,bot4_real,bot5_real
TELEGRAM_LOG_CHANNEL=-100123456789
REDIS_HOST=redis
```

### 3. Desplegar con Docker Compose

```bash
# Primera vez - construir y levantar
docker-compose --env-file .env.docker up -d --build

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f --tail=100
```

### 4. Comandos de mantenimiento

```bash
# Reiniciar la aplicación
docker-compose restart retador

# Actualizar a nueva versión
git pull
docker-compose build --no-cache retador
docker-compose up -d retador

# Ver uso de recursos
docker stats

# Backup de Redis
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/
```

### 5. Límites de recursos (bmax90 - 24GB RAM)

| Servicio  | RAM Límite | RAM Reservada |
| --------- | ---------- | ------------- |
| retador   | 2 GB       | 512 MB        |
| redis     | 1 GB       | 256 MB        |
| **Total** | 3 GB       | 768 MB        |

> El servidor tiene 24GB, dejando ~21GB para otros servicios o escalado futuro.

---

## 📦 Gestión de Dependencias

### pyproject.toml (fuente de verdad)

```bash
# Instalar proyecto + deps
pip install -e .

# Instalar con deps de desarrollo
pip install -e ".[dev]"
```

### Generar requirements.txt

```bash
# Instalar pip-tools
pip install pip-tools

# Generar requirements.txt desde pyproject.toml
pip-compile pyproject.toml -o requirements.txt

# Actualizar deps a últimas versiones
pip-compile --upgrade pyproject.toml -o requirements.txt
```

### ¿Cuándo usar cada archivo?

| Archivo            | Cuándo usarlo                         |
| ------------------ | ------------------------------------- |
| `pyproject.toml`   | Añadir/quitar dependencias            |
| `requirements.txt` | Docker build, CI/CD, reproducibilidad |

---

## 🔄 Flujo de Trabajo Recomendado

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   DESARROLLO    │────▶│     TESTS       │────▶│   PRODUCCIÓN    │
│   (Windows)     │     │    (Docker)     │     │    (bmax90)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   .venv local            docker-compose          docker-compose
   pytest unit/           pytest integ/           up -d --build
        │                       │                       │
   REDIS_HOST=            REDIS_HOST=             REDIS_HOST=
   localhost              redis                   redis
```

### Checklist antes de desplegar

- [ ] Tests unitarios pasan (`pytest tests/unit/`)
- [ ] Tests de integración pasan (`pytest tests/integration/`)
- [ ] Linting limpio (`ruff check src/`)
- [ ] `.env.docker` configurado con valores de producción
- [ ] Commit y push al repositorio

---

## 🛡️ Seguridad

| Archivo        | ¿En Git? | Contiene secretos   |
| -------------- | -------- | ------------------- |
| `.env`         | ❌ No     | ✅ Sí                |
| `.env.docker`  | ❌ No     | ✅ Sí                |
| `.env.example` | ✅ Sí     | ❌ No (placeholders) |

> **Nunca** subas archivos `.env` con tokens reales al repositorio.

---

## 📝 Referencia Rápida de Comandos

```bash
# === DESARROLLO LOCAL ===
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m scripts.run

# === DOCKER DESARROLLO ===
docker-compose --env-file .env.docker -f docker-compose.yml -f docker-compose.dev.yml up

# === DOCKER PRODUCCIÓN ===
docker-compose --env-file .env.docker up -d --build
docker-compose logs -f
docker-compose restart retador

# === MANTENIMIENTO ===
docker-compose down
docker system prune -f
docker-compose build --no-cache
```
