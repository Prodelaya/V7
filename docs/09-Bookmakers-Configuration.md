# Configuración de Bookmakers - Diseño Técnico

> **Tipo**: Documento de Referencia Técnica  
> **Versión**: 1.0  
> **Última actualización**: Diciembre 2025  
> **Estado**: Diseño aprobado (pendiente de implementación en Fase 4)

---

## 1. Resumen Ejecutivo

Este documento describe el diseño técnico para la configuración de casas de apuestas (bookmakers) en Retador v2.0. El sistema requiere múltiples listas de bookmakers para diferentes propósitos:

1. **API_BOOKMAKERS**: Bookmakers consultados en la API de surebets
2. **SHARP_BOOKMAKERS**: Casas de referencia para cálculos
3. **TARGET_BOOKIES**: Casas donde se envían picks a usuarios
4. **BOOKMAKER_CHANNELS**: Canales de Telegram por bookmaker
5. **BOOKIE_CONTRAPARTIDAS**: Contrapartidas permitidas por target

---

## 2. Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE BOOKMAKERS EN EL SISTEMA                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  .env                                                                        │
│   │                                                                          │
│   ├──► API_BOOKMAKERS ──────► SurebetClient ──────► API Request             │
│   │    "source" param                              ?source=bk1|bk2|...       │
│   │                                                                          │
│   ├──► SHARP_BOOKMAKERS ────► Surebet.from_api_response()                   │
│   │    Identifica prong_sharp                                                │
│   │                                                                          │
│   ├──► TARGET_BOOKIES ──────► PickHandler ────────► Filtrado + Canal        │
│   │    Casas destino                                                         │
│   │                                                                          │
│   ├──► BOOKMAKER_CHANNELS ──► TelegramGateway ────► Envío a canal           │
│   │    ID canales TG                                                         │
│   │                                                                          │
│   └──► BOOKIE_CONTRAPARTIDAS ► Validación de pares sharp-soft               │
│        (Opcional)                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Definición de Cada Configuración

### 3.1 API_BOOKMAKERS

**Propósito**: Lista de bookmakers que se envían como parámetro `source` en la petición a la API de surebets.

**Características**:
- Debe incluir TODOS los bookmakers de interés (sharps + targets)
- Se concatenan con `|` para la URL
- Más bookmakers = más surebets potenciales, pero más procesamiento

**Ejemplo de uso**:
```python
# URL resultante:
# GET /request?product=surebets&source=pinnaclesports|retabet_apuestas|yaasscasino
params = {
    "source": "|".join(settings.API_BOOKMAKERS)
}
```

**Formato en .env**:
```env
API_BOOKMAKERS=pinnaclesports,retabet_apuestas,yaasscasino,bet365
```

---

### 3.2 SHARP_BOOKMAKERS

**Propósito**: Identificar qué casas de apuestas son "sharp" (profesionales/referencia).

**Características**:
- Se usa en `Surebet.from_api_response()` para determinar qué prong es el sharp
- Típicamente solo `pinnaclesports` (Pinnacle)
- Las odds del sharp son la referencia para calcular si hay valor

**Ejemplo de uso**:
```python
# En Surebet.from_api_response():
if prong1_bookmaker in sharp_bookmakers:
    prong_sharp = prong1
    prong_soft = prong2
```

**Formato en .env**:
```env
SHARP_BOOKMAKERS=pinnaclesports
```

**Estado actual**: Constante hardcodeada en `src/domain/entities/surebet.py`:
```python
SHARP_BOOKMAKERS: FrozenSet[str] = frozenset({
    "pinnaclesports",
})
```

---

### 3.3 TARGET_BOOKIES

**Propósito**: Lista de casas de apuestas donde el usuario puede apostar (sus "targets").

**Características**:
- Se usa para filtrar surebets relevantes
- Se usa para asignar a qué canal de Telegram enviar cada pick
- Solo se envían picks donde el `prong_soft` es de un target

**Ejemplo de uso**:
```python
# En PickHandler:
if surebet.soft_bookmaker in settings.TARGET_BOOKIES:
    channel_id = settings.BOOKMAKER_CHANNELS[surebet.soft_bookmaker]
    await telegram.send_pick(channel_id, pick)
```

**Formato en .env**:
```env
TARGET_BOOKIES=retabet_apuestas,yaasscasino
```

---

### 3.4 BOOKMAKER_CHANNELS

**Propósito**: Mapear cada bookmaker target a un canal de Telegram específico.

**Características**:
- Cada target tiene su propio canal
- Permite a usuarios suscribirse solo a las casas que usan
- El ID del canal es un número negativo (formato Telegram API)

**Ejemplo de uso**:
```python
# En TelegramGateway:
channel_id = settings.BOOKMAKER_CHANNELS.get(bookmaker)
if channel_id:
    await bot.send_message(channel_id, message)
```

**Formato en .env**:
```env
BOOKMAKER_CHANNELS=retabet_apuestas=-1002294438792,yaasscasino=-1002360901387
```

---

### 3.5 BOOKIE_CONTRAPARTIDAS (Opcional/Avanzado)

**Propósito**: Definir qué sharps son válidos como contrapartida para cada target.

**Características**:
- Configuración avanzada
- Permite restringir combinaciones (ej: solo pinnacle vs retabet)
- Por defecto, cualquier sharp es válido

**Ejemplo de uso**:
```python
# Validación:
allowed_sharps = settings.BOOKIE_CONTRAPARTIDAS.get(soft_bookie, all_sharps)
if sharp_bookie in allowed_sharps:
    # Surebet válida
```

**Formato en .env**:
```env
BOOKIE_CONTRAPARTIDAS=retabet_apuestas=pinnaclesports,yaasscasino=pinnaclesports|bet365
```

---

## 4. Implementación en Pydantic Settings

### 4.1 Diseño de la Clase Settings (Fase 4)

```python
# src/config/settings.py

from typing import Dict, List, FrozenSet
from pydantic_settings import BaseSettings
from pydantic import field_validator

class BookmakerConfig(BaseSettings):
    """Configuración de bookmakers desde variables de entorno."""
    
    # Para la API
    API_BOOKMAKERS: List[str] = ["pinnaclesports"]
    
    # Casas sharp (referencia)
    SHARP_BOOKMAKERS: FrozenSet[str] = frozenset({"pinnaclesports"})
    
    # Casas target (donde apostamos)
    TARGET_BOOKIES: List[str] = []
    
    # Canales de Telegram por bookmaker
    BOOKMAKER_CHANNELS: Dict[str, int] = {}
    
    # Contrapartidas permitidas (opcional)
    BOOKIE_CONTRAPARTIDAS: Dict[str, List[str]] = {}
    
    @field_validator("API_BOOKMAKERS", "TARGET_BOOKIES", mode="before")
    @classmethod
    def parse_comma_separated(cls, v):
        """Parsea listas separadas por comas desde .env."""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
    
    @field_validator("SHARP_BOOKMAKERS", mode="before")
    @classmethod
    def parse_sharp_bookmakers(cls, v):
        """Parsea sharps a frozenset."""
        if isinstance(v, str):
            return frozenset(x.strip() for x in v.split(",") if x.strip())
        return frozenset(v) if v else frozenset()
    
    @field_validator("BOOKMAKER_CHANNELS", mode="before")
    @classmethod
    def parse_channels(cls, v):
        """Parsea formato 'bookie=channel_id,...'."""
        if isinstance(v, str):
            result = {}
            for pair in v.split(","):
                if "=" in pair:
                    bookie, channel = pair.split("=", 1)
                    result[bookie.strip()] = int(channel.strip())
            return result
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## 5. Relación con el Código Legacy

| Concepto V6 (Legacy)    | Concepto V7 (Nuevo)     | Ubicación |
| ----------------------- | ----------------------- | --------- |
| `config.BOOKMAKERS`     | `API_BOOKMAKERS`        | `.env`    |
| `BOOKIE_HIERARCHY`      | `SHARP_BOOKMAKERS`      | `.env`    |
| `TARGET_BOOKIES`        | `TARGET_BOOKIES`        | `.env`    |
| `BOOKMAKER_CHANNELS`    | `BOOKMAKER_CHANNELS`    | `.env`    |
| `BOOKIE_CONTRAPARTIDAS` | `BOOKIE_CONTRAPARTIDAS` | `.env`    |

---

## 6. Puntos de Integración

### 6.1 SurebetClient (infrastructure/api/)

```python
class SurebetClient:
    def __init__(self, settings: BookmakerConfig):
        self.bookmakers = settings.API_BOOKMAKERS
    
    def build_params(self) -> dict:
        return {
            "product": "surebets",
            "source": "|".join(self.bookmakers),
            # ...
        }
```

### 6.2 Surebet Entity (domain/entities/)

```python
@classmethod
def from_api_response(
    cls,
    data: dict,
    sharp_bookmakers: FrozenSet[str] | None = None  # Inyectado desde Settings
) -> Surebet:
    # Usa sharp_bookmakers para determinar roles
```

### 6.3 PickHandler (application/handlers/)

```python
class PickHandler:
    def __init__(self, settings: BookmakerConfig):
        self.targets = settings.TARGET_BOOKIES
        self.channels = settings.BOOKMAKER_CHANNELS
        self.sharps = settings.SHARP_BOOKMAKERS
    
    async def process_surebet(self, data: dict) -> None:
        surebet = Surebet.from_api_response(data, self.sharps)
        if surebet.soft_bookmaker in self.targets:
            channel = self.channels[surebet.soft_bookmaker]
            await self.telegram.send(channel, surebet.to_pick())
```

---

## 7. Archivo .env.example

```env
# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BOOKMAKERS - Retador v2.0
# ═══════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────
# 1. BOOKMAKERS PARA LA API
#    Lista de todas las casas a consultar (separadas por coma)
#    Debe incluir los sharps + todos los targets
# ──────────────────────────────────────────────────────────────────────────
API_BOOKMAKERS=pinnaclesports,retabet_apuestas,yaasscasino

# ──────────────────────────────────────────────────────────────────────────
# 2. CASAS SHARP (referencia para cálculos)
#    Normalmente solo Pinnacle
# ──────────────────────────────────────────────────────────────────────────
SHARP_BOOKMAKERS=pinnaclesports

# ──────────────────────────────────────────────────────────────────────────
# 3. CASAS TARGET (donde el usuario apuesta)
#    Solo los picks de estas casas se enviarán
# ──────────────────────────────────────────────────────────────────────────
TARGET_BOOKIES=retabet_apuestas,yaasscasino

# ──────────────────────────────────────────────────────────────────────────
# 4. CANALES DE TELEGRAM POR BOOKMAKER
#    Formato: nombre_bookie=id_canal_telegram
#    Los IDs de canal son números negativos
# ──────────────────────────────────────────────────────────────────────────
BOOKMAKER_CHANNELS=retabet_apuestas=-1002294438792,yaasscasino=-1002360901387

# ──────────────────────────────────────────────────────────────────────────
# 5. CONTRAPARTIDAS PERMITIDAS (OPCIONAL - avanzado)
#    Formato: target=sharp1|sharp2
#    Si no se especifica, cualquier sharp es válido para cualquier target
# ──────────────────────────────────────────────────────────────────────────
# BOOKIE_CONTRAPARTIDAS=retabet_apuestas=pinnaclesports,yaasscasino=pinnaclesports
```

---

## 8. Validaciones Requeridas

1. **Consistencia**: Cada `TARGET_BOOKIE` debe tener un `BOOKMAKER_CHANNEL` asociado
2. **Inclusión**: Todos los `TARGET_BOOKIES` + `SHARP_BOOKMAKERS` deben estar en `API_BOOKMAKERS`
3. **No vacío**: `SHARP_BOOKMAKERS` debe tener al menos un valor
4. **Formato de IDs**: Los IDs de canal deben ser enteros válidos

---

## 9. Tareas de Implementación (Fase 4)

- [ ] **4.1**: Crear clase `BookmakerConfig` en `src/config/settings.py`
- [ ] **4.2**: Implementar validadores Pydantic para parseo de listas
- [ ] **4.3**: Actualizar `.env.example` con todas las variables
- [ ] **4.4**: Actualizar `Surebet.from_api_response()` para recibir sharps inyectados
- [ ] **4.5**: Integrar con `SurebetClient`
- [ ] **4.6**: Integrar con `PickHandler`
- [ ] **4.7**: Tests de configuración

---

## 10. Referencias

- [Legacy Code: RetadorV6.py](../legacy/RetadorV6.py) - Líneas 282-356
- [API Documentation](./08-API-Documentation.md) - Parámetro `source`
- [Implementation Plan](./05-Implementation.md) - Fase 4: Configuración
