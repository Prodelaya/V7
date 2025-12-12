"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ⚠️  CÓDIGO LEGACY - V6  ⚠️                          ║
║                                                                              ║
║  Este archivo es la versión anterior del sistema (monolito de ~2000 líneas). ║
║  Se mantiene como REFERENCIA para la migración a v2.0 (Clean Architecture). ║
║                                                                              ║
║  ❌ NO MODIFICAR - NO USAR EN PRODUCCIÓN                                     ║
║  ✅ USAR COMO REFERENCIA para entender lógica de negocio                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

CONTEXTO DEL PROYECTO:
    Sistema de detección y distribución de apuestas de valor (value bets).
    Consume API de surebets, filtra oportunidades y envía picks por Telegram.
    
DOCUMENTACIÓN DE REFERENCIA:
    - docs/SRS.md: Requisitos funcionales y no funcionales
    - docs/PDR.md: Diseño preliminar y arquitectura v2.0
    - docs/ADR.md: Decisiones arquitectónicas y justificaciones

═══════════════════════════════════════════════════════════════════════════════
                        GUÍA DE REUTILIZACIÓN POR COMPONENTE
═══════════════════════════════════════════════════════════════════════════════

✅ REUTILIZABLE (copiar y adaptar):
──────────────────────────────────
│ Clase/Método              │ Destino v2.0                      │ Notas                           │
├───────────────────────────┼───────────────────────────────────┼─────────────────────────────────┤
│ BotConfig                 │ config/settings.py                │ Migrar a Pydantic Settings      │
│ TelegramLogHandler        │ config/logging_config.py          │ Sin cambios significativos      │
│ ConnectionManager         │ infrastructure/api/               │ Reutilizar gestión de sesiones  │
│ opposite_markets (dict)   │ domain/services/opposite_market   │ Diccionario de mercados opuestos│
│ MessageFormatter.*        │ infrastructure/messaging/         │ Ver notas sobre cache HTML      │
│   - safe_escape()         │                                   │ ✅ Reutilizar                   │
│   - clean_text()          │                                   │ ✅ Reutilizar                   │
│   - format_date()         │                                   │ ✅ Reutilizar                   │
│   - ajustar_dominio()     │                                   │ ✅ Reutilizar                   │
│   - message_template      │                                   │ ✅ Reutilizar                   │
│ TelegramSender            │ infrastructure/messaging/         │ Adaptar para heap priorizado    │
│   - _enforce_rate_limit() │                                   │ ✅ Lógica de ventana deslizante │
│   - send_message_opt...() │                                   │ ✅ Multi-bot y rotación         │

⚠️  REUTILIZAR CON MODIFICACIONES:
──────────────────────────────────
│ Clase/Método              │ Destino v2.0                      │ Modificación requerida          │
├───────────────────────────┼───────────────────────────────────┼─────────────────────────────────┤
│ RedisHandler              │ infrastructure/repositories/      │ SIN Bloom Filter (ver ADR-012)  │
│   - _get_complete_key()   │                                   │ ✅ Reutilizar lógica de claves  │
│   - get_market_opposites()│                                   │ ✅ Mover a domain/services      │
│   - is_pick_sent_batch()  │                                   │ ⚠️ Simplificar, usar pipeline   │
│   - mark_picks_sent_bat() │                                   │ ⚠️ Await obligatorio (ADR-013)  │
│ RequestQueue.fetch_picks()│ infrastructure/api/surebet_client │ ➕ Añadir cursor incremental    │
│                           │                                   │ ➕ Añadir params optimizados    │
│ validate_pick()           │ domain/rules/validators/          │ Separar en Chain of Respons.    │
│ determine_bet_roles()     │ domain/services/                  │ Extraer a servicio de dominio   │

❌ NO REUTILIZAR (obsoleto o con bugs):
───────────────────────────────────────
│ Clase/Método              │ Razón                             │ Referencia                      │
├───────────────────────────┼───────────────────────────────────┼─────────────────────────────────┤
│ calculate_min_odds()      │ ❌ FÓRMULA INCORRECTA             │ Ver ADR-003 para fórmula ok     │
│                           │ Acepta ~-3% creyendo que es -1%   │ Correcto: 1/(1.01 - 1/odd_pin)  │
│ get_stake() [Bet365 branch│ ❌ Lógica inconsistente           │ Solo usar rama Pinnacle         │
│ Workers (validation_,     │ ❌ Reemplazado por asyncio.gather │ Ver ADR-014                     │
│   redis_, telegram_worker)│                                   │                                 │
│ Colas internas            │ ❌ Añaden latencia innecesaria    │ Ver ADR-014                     │
│   (validation_queue, etc) │                                   │                                 │
│ OptimizedPrefetchManager  │ ❌ Reemplazar por cursor increm.  │ Ver ADR-009                     │
│ ConcurrencyManager        │ ❌ Ya no se usa                   │ Semáforo directo si necesario   │

═══════════════════════════════════════════════════════════════════════════════
                              BUGS CONOCIDOS EN V6
═══════════════════════════════════════════════════════════════════════════════

🔴 BUG CRÍTICO - calculate_min_odds() [línea ~870]:
    ACTUAL:     oddmin = 1 / (margin - prob_contraria - (1/100))
    CORRECTO:   oddmin = 1 / (1.01 - 1/odd_pinnacle)
    IMPACTO:    Acepta picks con -3% de profit real creyendo que el límite es -1%
    PÉRDIDA:    Estimada ~900€/mes por cada 1000€/día apostados
    
🟡 BUG MENOR - get_stake() rama Bet365 [línea ~850]:
    Solo acepta profit >= 2%, contradice la lógica de negocio (debería ser más permisivo)
    
🟡 INEFICIENCIA - Workers/Colas [líneas ~1270-1380]:
    3 colas internas añaden ~15-30ms de latencia innecesaria
    Reemplazar por asyncio.gather directo

═══════════════════════════════════════════════════════════════════════════════
                         MAPEO CÓDIGO ANTIGUO → COMPONENTES V2.0
═══════════════════════════════════════════════════════════════════════════════

TelegramLogHandler    → config/logging_config.py
BotConfig             → config/settings.py (Pydantic)
ConnectionManager     → infrastructure/api/connection.py
RequestQueue          → infrastructure/api/surebet_client.py
OptimizedPrefetch...  → ELIMINAR (usar cursor)
CacheManager          → infrastructure/cache/local_cache.py
RedisHandler          → infrastructure/repositories/redis_repo.py
MessageFormatter      → infrastructure/messaging/message_formatter.py
TelegramSender        → infrastructure/messaging/telegram_gateway.py
BettingBot            → DESCOMPONER en:
                                          - application/handlers/pick_handler.py
                                          - domain/rules/validators/
                                          - domain/services/calculation_service.py

═══════════════════════════════════════════════════════════════════════════════
                              INSTRUCCIONES PARA AGENTES
═══════════════════════════════════════════════════════════════════════════════

1. ANTES de implementar cualquier componente, consultar:
   - docs/SRS.md para requisitos
   - docs/PDR.md para arquitectura destino
   - docs/ADR.md para decisiones y justificaciones

2. NUNCA copiar calculate_min_odds() - usar fórmula de ADR-003

3. Al migrar RedisHandler:
   - NO implementar Bloom Filter (ADR-012)
   - NO usar fire-and-forget (ADR-013)
   - SÍ usar pipeline batch para exists()

4. Al migrar RequestQueue:
   - AÑADIR cursor incremental (ADR-009)
   - AÑADIR polling adaptativo (ADR-010)
   - AÑADIR params: order=created_at_desc, min-profit=-1

5. Al migrar TelegramSender:
   - AÑADIR heap priorizado por profit (ADR-006)
   - MANTENER lógica de multi-bot y rotación

6. Estructura destino: Clean Architecture
   src/
   ├── domain/         # Lógica pura, sin I/O
   ├── application/    # Casos de uso, orquestación  
   ├── infrastructure/ # Adaptadores externos
   └── config/         # Configuración

═══════════════════════════════════════════════════════════════════════════════
"""

# Standard Library
import asyncio
from asyncio import exceptions
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import config
import time
import os  # GestiÃ³n de rutas y operaciones del sistema
import gc  # RecolecciÃ³n de basura manual
import re  # Expresiones regulares
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field  # DefiniciÃ³n de clases de datos
from typing import Any, List, Dict, Optional, Tuple  # Tipos para anotaciones
from pytz import timezone as pytz_timezone, UTC  # GestiÃ³n de zonas horarias
import html  # Para escapar caracteres HTML
import random
import statistics
import collections
import asyncpg

# Third-Party Libraries
import aiohttp
from aiohttp import ClientSession
import pytz
import orjson  # OptimizaciÃ³n para lectura/escritura de JSON
from redis import asyncio as aioredis  # Cliente asÃ­ncrono para Redis
import aiogram
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramForbiddenError
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import GetUpdates
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

#Envio de errores por telegram
class TelegramLogHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: int):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.min_level_telegram = logging.WARNING
        self.last_messages = {}
        self.duplicate_timeout = 1800
        self.telegram_lock = asyncio.Lock()
        self._message_queue = asyncio.Queue()
        self._background_task = None

    def emit(self, record):
        if record.levelno < self.min_level_telegram:
            return

        try:
            msg = self.format(record)
            current_time = time.time()
            
            mensaje_base = f"{record.levelname}:{record.message}"
            msg_hash = hash(mensaje_base)
            
            if msg_hash in self.last_messages:
                if current_time - self.last_messages[msg_hash] < self.duplicate_timeout:
                    return
                    
            self.last_messages[msg_hash] = current_time
            self.last_messages = {
                k: v for k, v in self.last_messages.items()
                if current_time - v < self.duplicate_timeout
            }
            
            if self._background_task is None or self._background_task.done():
                self._background_task = asyncio.create_task(self._background_sender())
            
            asyncio.create_task(self._message_queue.put((msg, record.levelname)))
        
        except Exception as e:
            print(f"Error en TelegramLogHandler: {e}")

    async def _background_sender(self):
        while True:
            try:
                msg, level = await self._message_queue.get()
                async with self.telegram_lock:
                    bot = Bot(token=self.bot_token)
                    try:
                        emoji = "ðŸ”´" if level == "ERROR" else "ðŸŸ¡"
                        formatted_message = f"{emoji} <b>{level}</b>\n<pre>{html.escape(msg)}</pre>"  # â† HTML
                        
                        await bot.send_message(
                            chat_id=self.chat_id,
                            text=formatted_message,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                    finally:
                        await bot.session.close()
            except Exception as e:
                print(f"Error en background sender: {e}")
            await asyncio.sleep(0.1)



# ConfiguraciÃ³n bÃ¡sica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    # ConfiguraciÃ³n de APIs y tokens
    API_URL: str = REDACTED_API_URL
    API_TOKEN: str = 'REDACTED_API_TOKEN'
    TELEGRAM_TOKENS: List[str] = field(default_factory=lambda: [
        'REDACTED_TELEGRAM_TOKEN_1',
        'REDACTED_TELEGRAM_TOKEN_2',
        'REDACTED_TELEGRAM_TOKEN_3',
        'REDACTED_TELEGRAM_TOKEN_4',
        'REDACTED_TELEGRAM_TOKEN_5'
    ])

    # Control de peticiones y rate limiting
    REQUEST_RATE_LIMIT: int = 2          # MÃ¡ximo de peticiones por segundo permitido por el proveedor
    REQUEST_TIMEOUT: int = 10            # Tiempo mÃ¡ximo de espera para peticiones
    REQUEST_RETRIES: int = 3             # NÃºmero de reintentos por peticiÃ³n
    BASE_DELAY: float = 1.0              # Delay base para reintentos
    SLEEP_INTERVAL: float = 0.05         # Intervalo entre intentos de peticiones
    
    # GestiÃ³n de sesiÃ³n HTTP (simplificada)
    SESSION_MAX_AGE: int = 43200         # 12 horas - Vida mÃ¡xima de una sesiÃ³n
    MAX_ERRORS_PER_SESSION: int = 10     # Aumentado ya que manejamos una Ãºnica sesiÃ³n
    
    CONNECTIONS_PER_HOST: int = 10        # LÃ­mite de conexiones por host
    DNS_CACHE_TTL: int = 300             # TTL para cachÃ© DNS
    
    # ConfiguraciÃ³n de cachÃ©
    CACHE_TTL: int = 10                  # Tiempo de vida del cachÃ©
    CACHE_MAX_SIZE: int = 2000           # TamaÃ±o mÃ¡ximo del cachÃ©
      
    # ParÃ¡metros de la API
    LIMIT: int = 5000                    # LÃ­mite de registros por peticiÃ³n
    PRODUCT: str = 'surebets'            # Tipo de producto a consultar
    SPORTS: List[str] = field(default_factory=lambda: [
        'AmericanFootball', 'Badminton', 'Baseball', 'Basketball', 'CounterStrike',
        'Cricket', 'Darts', 'E_Football', 'Football', 'Futsal', 'Handball',
        'Hockey', 'LeagueOfLegends', 'Rugby', 'Snooker', 'TableTennis',
        'Tennis', 'Valorant', 'Volleyball', 'WaterPolo'
    ])

    # ConfiguraciÃ³n de casas de apuestas y sus contrapartidas permitidas
    BOOKIE_CONTRAPARTIDAS: Dict[str, List[str]] = field(default_factory=lambda: {
        'retabet_apuestas': ['pinnaclesports'],
        #'bet365': ['pinnaclesports'],
        #'winamax_es': ['pinnaclesports','bet2365'],
        'yaasscasino': ['pinnaclesports'],
        #'sportium': ['pinnaclesports'],
        #'versus': ['pinnaclesports','bet365'],
        #'bwin': ['pinnaclesports','bet365'],
        #'pokerstars_uk': ['pinnaclesports'],
        #'caliente': ['pinnaclesports']
        #'admiral_at': ['pinnaclesports']
        #'betway': ['pinnaclesports']
    })

    # ConfiguraciÃ³n de casas de apuestas
    BOOKIE_HIERARCHY: List[str] = field(default_factory=lambda: [
        'pinnaclesports',
        'bet365',
    ])
    
    TARGET_BOOKIES: List[str] = field(default_factory=lambda: [
        'retabet_apuestas',
        #'sportium',
        #'caliente',
        #'bet365',
        #'winamax_es',
        #'versus',
        'yaasscasino',
        #'pokerstars_uk',
        #'admiral_at',
        #'bwin',
        #'betway'
    
        
    ])
    
    BOOKMAKERS: List[str] = field(default_factory=lambda: [
        'pinnaclesports',
        #'betway',
        #'bet365',
        'retabet_apuestas',
        #'sportium',
        #'caliente',
        #'winamax_es',
        #'versus',
        #'pokerstars_uk',
        #'admiral_at',

        'yaasscasino',
        #'bwin'
    ])
    
    BOOKMAKER_CHANNELS: Dict[str, int] = field(default_factory=lambda: {
        'retabet_apuestas': REDACTED_CHANNEL_ID_1,
        'bet365': REDACTED_CHANNEL_ID_2,
        'winamax_es': REDACTED_CHANNEL_ID_3,
        'yaasscasino': REDACTED_CHANNEL_ID_4,
        'bwin': REDACTED_CHANNEL_ID_5,
        'sportium':REDACTED_CHANNEL_ID_6,
        'pokerstars_uk':REDACTED_CHANNEL_ID_7,
        #'caliente':REDACTED_CHANNEL_ID_8,
        'betway': REDACTED_CHANNEL_ID_9,
        'admiral_at': REDACTED_CHANNEL_ID_10,
        'versus': REDACTED_CHANNEL_ID_11
    })

    LOG_CHANNEL_ID: int = REDACTED_LOG_CHANNEL_ID  # ID del canal donde quieres recibir los logs
    
    # LÃ­mites de tiempo y validaciÃ³n
    MIN_ODDS: float = 1.1                # Cuota mÃ­nima aceptable
    MAX_ODDS: float = 9.99               # Cuota mÃ¡xima aceptable
    MIN_EVENT_TIME: int = 0            # Tiempo mÃ­nimo en segundos
    
    # Control de concurrencia
    CONCURRENT_PICKS: int = 250           # Procesamiento paralelo de picks
    CONCURRENT_REQUESTS: int = 100        # Peticiones HTTP concurrentes
    

class ConnectionManager:
    def __init__(self, config: BotConfig):
        """
        Inicializa el ConnectionManager con la configuraciÃ³n centralizada.
        """
        self.config = config
        self.session = None
        self.session_created_at = None
        self.session_errors = 0
        self.session_lock = asyncio.Lock()
        self.maintenance_task = None
        self.is_shutting_down = False
        
        # Timeouts optimizados
        self.timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=15,
            sock_connect=10
        )
        
        # Conector TCP con parÃ¡metros optimizados
        # Quitamos keepalive_timeout ya que usamos force_close=True
        self.connector = aiohttp.TCPConnector(
            limit=config.CONCURRENT_REQUESTS * 2,
            limit_per_host=config.CONNECTIONS_PER_HOST * 2,
            enable_cleanup_closed=True,
            force_close=True,  # True para evitar conexiones zombies
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        # Periodo de enfriamiento entre sesiones
        self.session_cooling_period = 30

    async def create_session(self) -> aiohttp.ClientSession:
        """Crea una nueva sesiÃ³n HTTP con mejor manejo de errores."""
        try:
            if self.session and not self.session.closed:
                await self.cleanup_session()
                
            logger.info("Creando nueva sesiÃ³n HTTP")
            return aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.API_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
        except Exception as e:
            logger.error(f"Error creando sesiÃ³n: {e}")
            await asyncio.sleep(5)
            return None

    async def cleanup_session(self):
        """Limpieza exhaustiva de la sesiÃ³n actual."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                
            # Cerrar todas las conexiones pendientes
            if self.connector and not self.connector.closed:
                await self.connector.close()
                
            # Recrear el conector
            self.connector = aiohttp.TCPConnector(
                limit=self.config.CONCURRENT_REQUESTS * 2,
                limit_per_host=self.config.CONNECTIONS_PER_HOST * 2,
                enable_cleanup_closed=True,
                force_close=True,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            # Forzar recolecciÃ³n de basura
            gc.collect()
            
            # Esperar para asegurar que todo se ha cerrado
            await asyncio.sleep(self.session_cooling_period)
            
        except Exception as e:
            logger.error(f"Error en cleanup_session: {e}")

    async def get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesiÃ³n con mejor manejo de renovaciÃ³n."""
        if self.is_shutting_down:
            return None
            
        async with self.session_lock:
            current_time = time.time()
            
            # Verificar si necesitamos renovar la sesiÃ³n
            if (self.session and not self.session.closed and 
                self.session_created_at and 
                (current_time - self.session_created_at > self.config.SESSION_MAX_AGE or 
                self.session_errors >= self.config.MAX_ERRORS_PER_SESSION)):
                
                logger.info("Iniciando renovaciÃ³n proactiva de sesiÃ³n")
                await self.cleanup_session()
                self.session = None
                self.session_errors = 0
            
            if not self.session or self.session.closed:
                self.session = await self.create_session()
                if self.session:
                    self.session_created_at = current_time
                    self.session_errors = 0
                else:
                    raise RuntimeError("No se pudo crear una nueva sesiÃ³n")

            if not self.maintenance_task or self.maintenance_task.done():
                self.maintenance_task = asyncio.create_task(self.maintain_session())
                
            return self.session

    async def maintain_session(self):
        """Mantenimiento periÃ³dico de la sesiÃ³n."""
        while not self.is_shutting_down:
            try:
                await asyncio.sleep(30)
                async with self.session_lock:
                    current_time = time.time()
                    
                    if self.session and not self.session.closed:
                        session_age = current_time - (self.session_created_at or 0)
                        should_refresh = (
                            session_age > self.config.SESSION_MAX_AGE or 
                            self.session_errors >= self.config.MAX_ERRORS_PER_SESSION
                        )
                        
                        if should_refresh:
                            logger.info(f"Renovando sesiÃ³n despuÃ©s de {session_age/3600:.1f} horas")
                            await self.cleanup_session()
                            self.session = await self.create_session()
                            self.session_created_at = current_time
                            self.session_errors = 0
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en mantenimiento de sesiÃ³n: {e}")
                await asyncio.sleep(5)

    async def cleanup(self):
        """Limpieza mejorada de recursos."""
        self.is_shutting_down = True
        
        try:
            if self.maintenance_task and not self.maintenance_task.cancelled():
                self.maintenance_task.cancel()
                try:
                    await self.maintenance_task
                except asyncio.CancelledError:
                    pass
            
            await self.cleanup_session()
            
        except Exception as e:
            logger.error(f"Error durante la limpieza: {e}")


class RequestQueue:
    def __init__(self, config: BotConfig, connection_manager: ConnectionManager):
        """
        Inicializa la cola de peticiones con gestiÃ³n de rate limit y cachÃ©.
        
        Args:
            config: ConfiguraciÃ³n central del bot
            connection_manager: Gestor de conexiones HTTP
        """
        self.config = config
        self.connection_manager = connection_manager
        
        # Control de rate limit usando una cola circular para timestamps
        self.last_request_times = collections.deque(maxlen=config.REQUEST_RATE_LIMIT)
        self.request_lock = asyncio.Lock()
        
        # Sistema de cachÃ© para resultados
        self.results_cache = {}
        self.cleanup_task = None

    async def _enforce_rate_limit(self):
        """
        Controla el rate limit asegurando no mÃ¡s de N peticiones por segundo.
        Usa un sistema de ventana deslizante para mayor precisiÃ³n.
        """
        async with self.request_lock:
            current_time = time.time()
            
            # Limpiar timestamps antiguos (mÃ¡s de 1 segundo)
            while (self.last_request_times and 
                   current_time - self.last_request_times[0] > 1.0):
                self.last_request_times.popleft()
            
            # Si alcanzamos el lÃ­mite, esperar el tiempo necesario
            if len(self.last_request_times) >= self.config.REQUEST_RATE_LIMIT:
                wait_time = 1.0 - (current_time - self.last_request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self.last_request_times.append(current_time)

    async def execute_request(self, method: str, url: str, **kwargs):
        """
        Ejecuta una peticiÃ³n HTTP respetando el rate limit y manejando reintentos.
        
        Args:
            method: MÃ©todo HTTP (GET, POST, etc)
            url: URL del endpoint
            **kwargs: Argumentos adicionales para la peticiÃ³n
            
        Returns:
            dict: Respuesta JSON de la API o None si falla
        """
        for attempt in range(self.config.REQUEST_RETRIES):
            try:
                await self._enforce_rate_limit()
                session = await self.connection_manager.get_session()
                
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    if response.status == 429:  # Rate limit excedido
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    # Incrementar contador de errores y esperar antes de reintentar
                    self.connection_manager.session_errors += 1
                    await asyncio.sleep(self.config.BASE_DELAY * (2 ** attempt))
                    
            except Exception as e:
                self.connection_manager.session_errors += 1
                logger.error(f"Error en peticiÃ³n (intento {attempt + 1}): {e}")
                await asyncio.sleep(self.config.BASE_DELAY * (2 ** attempt))
                
        return None

    async def fetch_picks(self, params: dict = None) -> List[dict]:
        """
        Obtiene picks de la API con soporte de cachÃ©.
        
        Args:
            params: ParÃ¡metros de la peticiÃ³n. Si es None, usa configuraciÃ³n por defecto
            
        Returns:
            List[dict]: Lista de picks o lista vacÃ­a si hay error
        """
        if params is None:
            params = {
                'product': self.config.PRODUCT,
                'limit': self.config.LIMIT,
                'source': '|'.join(self.config.BOOKMAKERS),
                'sport': '|'.join(self.config.SPORTS),
                'order': 'value_desc'
            }
            
        cache_key = f"{params.get('product')}:{params.get('source')}"
        current_time = time.time()
        
        # Verificar cachÃ©
        if cache_key in self.results_cache:
            cache_time, cache_data = self.results_cache[cache_key]
            if current_time - cache_time < self.config.CACHE_TTL:
                return cache_data

        try:
            data = await self.execute_request('GET', self.config.API_URL, params=params)
            if data and 'records' in data:
                # Ordenar los picks por profit de manera descendente
                sorted_picks = sorted(
                    data['records'],
                    key=lambda x: float(x.get('profit', 0)),
                    reverse=True
                )
                self.results_cache[cache_key] = (current_time, sorted_picks)
                return sorted_picks
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo picks: {e}")
            return []

    async def start_cache_cleanup(self):
        """Inicia la tarea de limpieza periÃ³dica de cachÃ©."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._periodic_cache_cleanup())

    async def _periodic_cache_cleanup(self):
        """Limpia periÃ³dicamente entradas antiguas del cachÃ©."""
        while True:
            try:
                await asyncio.sleep(30)
                current_time = time.time()
                
                self.results_cache = {
                    k: (t, d) for k, (t, d) in self.results_cache.items()
                    if current_time - t < self.config.CACHE_TTL
                }
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en limpieza de cachÃ©: {e}")

    async def cleanup(self):
        """Limpia recursos y cancela tareas pendientes."""
        if self.cleanup_task and not self.cleanup_task.cancelled():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            
        self.results_cache.clear()
        self.last_request_times.clear()
        

# Controlar concurrencia y respetar rate limits.
class ConcurrencyManager:
    def __init__(self, config: BotConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.CONCURRENT_REQUESTS)

    async def execute(self, func, *args, **kwargs):
        try:
            async with asyncio.timeout(self.config.REQUEST_TIMEOUT):
                async with self.semaphore:
                    return await func(*args, **kwargs)
        except asyncio.TimeoutError:
            logger.error(f"Timeout despuÃ©s de {self.config.REQUEST_TIMEOUT}s")
            raise
        except Exception as e:
            logger.error(f"Error en ejecuciÃ³n concurrente: {e}")
            raise


class OptimizedPrefetchManager:
    def __init__(self, config: BotConfig, request_queue: RequestQueue):
        self.config = config
        self.request_queue = request_queue
        self.prefetch_queue = asyncio.Queue(maxsize=config.CACHE_MAX_SIZE)
        self.is_running = False
        self.fetch_task = None

    async def _fetch_next_batch(self) -> Optional[List[dict]]:
        """Obtener siguiente lote de datos"""
        try:
            return await self.request_queue.fetch_picks()
        except Exception as e:
            logger.error(f"Error en prefetch: {e}")
            return None

    async def start_prefetching(self):
        """Iniciar prefetch continuo"""
        self.is_running = True
        self.fetch_task = asyncio.create_task(self._prefetch_loop())

    async def _prefetch_loop(self):
        """Loop principal de prefetch"""
        while self.is_running:
            try:
                if not self.prefetch_queue.full():
                    data = await self._fetch_next_batch()
                    if data:
                        await self.prefetch_queue.put(data)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error en ciclo de prefetch: {e}")
                await asyncio.sleep(1)

    async def get_next_data(self) -> Optional[List[dict]]:
        """Obtener siguiente conjunto de datos del buffer"""
        try:
            return await self.prefetch_queue.get()
        except Exception as e:
            logger.error(f"Error obteniendo datos del buffer: {e}")
            return None

    async def cleanup(self):
        """Limpieza de recursos"""
        self.is_running = False
        if self.fetch_task and not self.fetch_task.cancelled():
            self.fetch_task.cancel()
            try:
                await self.fetch_task
            except asyncio.CancelledError:
                pass
        
        # Limpiar cola de prefetch
        while not self.prefetch_queue.empty():
            try:
                self.prefetch_queue.get_nowait()
            except asyncio.QueueEmpty:
                break



# Borrados de cache auto
class CacheManager:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
        self.lock = asyncio.Lock()  # AÃ±adido lock para thread-safety
        self._cleanup_task = None
        self._last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    async def set(self, key: str, value: Any) -> None:
        """Establece un valor en la cachÃ© de manera thread-safe"""
        async with self.lock:
            current_time = time.time()
            self.cache[key] = value
            self.access_times[key] = current_time
            
            # Iniciar limpieza automÃ¡tica si es necesario
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._auto_cleanup())
            
            # Limpiar cache si excede el tamaÃ±o mÃ¡ximo
            if len(self.cache) > self.max_size:
                await self._cleanup(int(self.max_size * 0.2))



    async def _cleanup(self, num_entries: int) -> None:
        """Limpia un nÃºmero especÃ­fico de entradas mÃ¡s antiguas"""
        async with self.lock:
            if not self.access_times:
                return
                
            entries = sorted(self.access_times.items(), key=lambda x: x[1])
            to_remove = entries[:num_entries]
            
            for key, _ in to_remove:
                del self.cache[key]
                del self.access_times[key]

    async def _auto_cleanup(self) -> None:
        """Tarea de limpieza automÃ¡tica"""
        while True:
            try:
                current_time = time.time()
                if current_time - self._last_cleanup >= self.cleanup_interval:
                    await self._cleanup(int(self.max_size * 0.1))
                    self._last_cleanup = current_time
                await asyncio.sleep(60)  # Verificar cada minuto
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error en auto_cleanup: {e}")
                await asyncio.sleep(60)

    async def clear(self) -> None:
        """Limpia toda la cachÃ©"""
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()

    async def cleanup(self) -> None:
        """Limpia recursos"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.clear()




# Gestion para validar picks con Redis
class RedisHandler:
    def __init__(self, host='localhost', port=6379, db=0, password='REDACTED_REDIS_PASSWORD', MIN_EVENT_TIME: int = 30):
        self.logger = logging.getLogger(__name__)

        self.pool = aioredis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=500,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.redis = aioredis.Redis(
            connection_pool=self.pool,
            username='retador',
            decode_responses=True,
            retry_on_timeout=True

        )

        self.MIN_EVENT_TIME = MIN_EVENT_TIME
        self.local_cache = CacheManager(max_size=2000)  # Aumentado el tamaÃ±o
        self._pipeline_size = 50
        self._cache_lock = asyncio.Lock()
        
        self.opposite_markets = {
            'ah1': 'ah2', 'ah2': 'ah1',
            'win1': 'win2', 'win2': 'win1',
            'winonly1': 'winonly2', 'winonly2': 'winonly1',
            'win1retx': 'win2retx', 'win2retx': 'win1retx',
            'over': 'under', 'under': 'over',
            'eover': 'e_under', 'e_under': 'eover',
            'even': 'odd', 'odd': 'even',
            'win1tonil': 'win2tonil', 'win2tonil': 'win1tonil',
            'clean_sheet_1': 'clean_sheet_2', 'clean_sheet_2': 'clean_sheet_1',
            '_1x': ['_x2', '_12'], '_x2': ['_1x', '_12'], '_12': ['_1x', '_x2'],
            'win1 qualify': 'win2 qualify',
            'BETWEENMARGINH1': 'BETWEENMARGINH2'
        }


    async def is_pick_sent_batch(self, picks: List[dict]) -> Dict[str, bool]:
        results = {}
        keys_to_check = []
        
        # VerificaciÃ³n en cachÃ© local primero
        for pick in picks:
            key = self._get_complete_key(pick)
            if self.local_cache.get(key):
                results[key] = True
            else:
                keys_to_check.append((key, pick))
        
        if not keys_to_check:
            return results
            
        # VerificaciÃ³n en Redis usando pipeline
        try:
            async with self.redis.pipeline(transaction=False) as pipe:
                for key, _ in keys_to_check:
                    pipe.exists(key)
                    
                pipe_results = await pipe.execute()
                
                for (key, pick), exists in zip(keys_to_check, pipe_results):
                    if exists:
                        await self.local_cache.set(key, True)
                    results[key] = bool(exists)
                    
                return results
                
        except Exception as e:
            logger.error(f"Error en verificaciÃ³n batch: {e}")
            return {key: False for key, _ in keys_to_check}

    async def mark_picks_sent_batch(self, picks: List[dict]) -> bool:
        """Guarda picks en Redis asegurando que la TTL sea la fecha del evento."""
        try:
            tz_spain = pytz_timezone("Europe/Madrid")
            current_time = datetime.now(UTC)  # Asegurar que la comparaciÃ³n sea en UTC

            async with self.redis.pipeline(transaction=True) as pipe:
                for pick in picks:
                    if not self._validate_pick_data(pick):
                        continue

                    # Obtener la fecha del evento en UTC y convertirla a segundos
                    event_time = int(str(pick['time'])[:-3])  # Eliminar milisegundos
                    
                    # Calcular el tiempo restante hasta el evento
                    ttl = max(60, event_time - int(current_time.timestamp()))  # MÃ­nimo 60s

                    if ttl <= 0:
                        continue  # Si el evento ya pasÃ³, no guardarlo

                    key = self._get_complete_key(pick)
                    pipe.setex(key, ttl, time.time())  # Guardar en Redis con TTL exacto
                    
                    await self.local_cache.set(key, True)
                    
                await pipe.execute()
                return True

        except Exception as e:
            logger.error(f"Error en guardado batch: {e}")
            return False







    def _normalize_string(self, text: str) -> str:
        """Normaliza strings para asegurar consistencia en las claves"""
        if not text:
            return ''
        # Eliminar caracteres especiales y normalizar espacios
        clean_text = re.sub(r'[^\w\s]', '', str(text).lower())
        return ' '.join(clean_text.split())

    def _get_spain_time(self, timestamp: int) -> datetime:
        """Convierte un timestamp a datetime en zona horaria de EspaÃ±a"""
        tz_spain = pytz_timezone("Europe/Madrid")
        try:
            # Convertir el timestamp eliminando los Ãºltimos 3 dÃ­gitos
            timestamp_seconds = int(str(timestamp)[:-3])
            # Convertir a datetime en UTC y luego a hora de EspaÃ±a
            return datetime.fromtimestamp(timestamp_seconds, tz=UTC).astimezone(tz_spain)
        except Exception as e:
            logger.error(f"Error convirtiendo timestamp: {e}")
            return datetime.now(tz_spain)
    
    def _validate_pick_data(self, pick: dict) -> bool:
        """Valida que el pick contenga todos los campos necesarios"""
        required_fields = ['teams', 'time', 'type', 'target_bookmaker']
        for field in required_fields:
            if not pick.get(field):
                logger.warning(f"Campo requerido faltante: {field}")
                return False
        if not pick['type'].get('type'):
            logger.warning("Campo type.type faltante")
            return False
        return True
    
    def _get_base_key(self, pick: dict) -> str:
        """Genera una clave base mÃ¡s robusta para Redis"""
        team1 = self._normalize_string(pick['teams'][0])
        team2 = self._normalize_string(pick['teams'][1])
        event_time = str(int(str(pick['time'])[:-3]))
        tournament = self._normalize_string(pick.get('tournament', ''))
        return f"{team1}:{team2}:{event_time}:{tournament}"
    
    def _get_market_key(self, base_key: str, market_type: str, bookmaker: str) -> str:
        """Genera la llave completa incluyendo el mercado y el bookmaker"""
        return f"{base_key}:{market_type}:{bookmaker}"

    def _get_complete_key(self, pick: dict) -> str:
        """Genera la clave Ãºnica para un pick."""
        try:
            teams = pick.get('teams', ['', ''])
            event_time = str(pick.get('time', ''))
            type_dict = pick.get('type', {})  # Primero obtenemos el diccionario type
            market_type = type_dict.get('type', '').lower()
            variety = type_dict.get('variety', '').lower()
            bookmaker = pick.get('target_bookmaker', '')
            
            return f"{teams[0]}:{teams[1]}:{event_time}:{market_type}:{variety}:{bookmaker}"
        except Exception as e:
            self.logger.error(f"Error generando clave completa: {e}")
            return ""
        

      
    def get_market_opposites(self, market_type: str) -> List[str]:
        
        try:
            # Si recibimos un diccionario (pick completo), extraemos el tipo de mercado
            if isinstance(market_type, dict):
                # Navegamos la estructura del pick para obtener el tipo
                market_type = market_type.get('type', {}).get('type', '').lower()
            else:
                # Si es un string, solo lo convertimos a minÃºsculas
                market_type = str(market_type).lower()
                
            # Obtenemos el opuesto del diccionario
            opposite = self.opposite_markets.get(market_type, [])
            
            # Convertimos a lista si es un string
            if isinstance(opposite, str):
                return [opposite]
            
            return opposite if opposite else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo mercados opuestos para {market_type}: {e}")
            return []

    def _get_opposite_keys(self, pick: dict) -> List[str]:
        """Genera las claves para los mercados opuestos de un pick."""
        try:
            teams = pick.get('teams', ['', ''])
            event_time = str(pick.get('time', ''))
            # Accedemos correctamente a type.type y type.variety
            type_dict = pick.get('type', {})  # Primero obtenemos el diccionario type
            market_type = type_dict.get('type', '').lower()
            variety = type_dict.get('variety', '').lower()
            bookmaker = pick.get('target_bookmaker', '')
            
            # Base comÃºn para todas las claves
            base = f"{teams[0]}:{teams[1]}:{event_time}"
            
            # Obtenemos los mercados opuestos
            opposite_types = self.get_market_opposites(market_type)
            
            # Generamos las claves completas para cada mercado opuesto
            return [f"{base}:{opp_type}:{bookmaker}" for opp_type in opposite_types]
            
        except Exception as e:
            self.logger.error(f"Error generando claves opuestas: {e}")
            return []
    
    async def is_any_market_stored(self, pick: dict) -> bool:
        """Verifica si un pick o su mercado opuesto ya estÃ¡ almacenado en Redis."""
        try:
            # Obtener clave principal
            original_key = self._get_complete_key(pick)
            
            # Verificar si ya fue enviado (cachÃ© local o Redis)
            if self.local_cache.get(original_key) or await self.redis.exists(original_key):
                return True

            # Obtener mercado opuesto basado en el tipo de mercado
            market_type = pick['type']['type'].lower()
            opposite_markets = self.get_market_opposites(market_type)  # Solo pasamos el string

            # Verificar si alguno de los mercados opuestos ya estÃ¡ en Redis
            base_key = f"{pick['teams'][0]}:{pick['teams'][1]}:{pick['time']}"
            for opp_market in opposite_markets:
                opp_key = f"{base_key}:{opp_market}:{pick['target_bookmaker']}"
                if self.local_cache.get(opp_key) or await self.redis.exists(opp_key):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error verificando mercados en Redis: {e}")
            return False



    async def store_market_and_opposites(self, pick: dict, ttl: int) -> bool:
        """Guarda el pick y sus mercados equivalentes en Redis."""
        try:
            key = self._get_complete_key(pick)
            market_type = pick['type']['type'].lower()
            opposite_markets = self.get_market_opposites(market_type)  # Usar string, no pick completo

            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.setex(key, ttl, time.time())
                await self.local_cache.set(key, True)

                # Guardar tambiÃ©n los mercados equivalentes
                base_key = f"{pick['teams'][0]}:{pick['teams'][1]}:{pick['time']}"
                for opp_market in opposite_markets:
                    opp_key = f"{base_key}:{opp_market}:{pick['target_bookmaker']}"
                    pipe.setex(opp_key, ttl, time.time())
                    await self.local_cache.set(opp_key, True)

                await pipe.execute()
                return True

        except Exception as e:
            self.logger.error(f"Error almacenando mercados en Redis: {e}")
            return False


    async def close(self):
        """Cierra la conexiÃ³n con Redis"""
        if self.redis:
            await self.redis.close()
    
# Formateo del mensaje
class MessageFormatter:
    def __init__(self):
        self._cache_ttl = 60
        self._message_cache = CacheManager(max_size=1000)
        self.logger = logging.getLogger(__name__)
        self.replacements = {
            'win1retx': 'DNB1',
            'win2retx': 'DNB2',
            'winonly1': 'WIN1',
            'winonly2': 'WIN2',
            'win1': 'WIN1',
            'win2': 'WIN2',
            '_1x': '1X',
            '_x2': 'X2',
            '_12': '12',
            'e_over': 'e over',
            'e_under': 'e under',
            'point': '',
            'overall': '',
            'regular': '',
            'overtime': '',
            'regulartime': '',
            'goals': '',
            'goal': '',
            'set': '',
            'points': '',
            'game': '',
            'total': '',
            'match': '',
            'matches': '',
            '(SECOND_YELLOW_IS_YELLOW_AND_RED_CARD)': ''
        }

        self.words_to_remove = {
            'point', 'points', 'overall', 'regular', 'overtime', 
            'goal', 'goals', 'regulartime', 'set', 'time', 'total',
            'game', 'games', 'match', 'matches', '(SECOND_YELLOW_IS_YELLOW_AND_RED_CARD)', 'total'
        }
        self.emoji_cache = {
            'football': 'âš½ï¸',
            'basketball': 'ðŸ€',
            'americanfootball': 'ðŸˆ',
            'rugby': 'ðŸ‰',
            'hockey': 'ðŸ’',
            'tennis': 'ðŸŽ¾',
            'tabletennis': 'ðŸ“',
            'handball': 'ðŸ¤¾ðŸ¼â€â™‚ï¸',
            'baseball': 'âš¾ï¸',
            'volleyball': 'ðŸ',
            'e_football': 'ðŸŽ®',
            'darts': 'ðŸŽ¯'
        }
        self.dias = {
            0: 'Lunes', 1: 'Martes', 2: 'MiÃ©rcoles', 3: 'Jueves',
            4: 'Viernes', 5: 'SÃ¡bado', 6: 'Domingo'
        }
        self.message_template = (
            "<b>{stake} {type_info} @{odds} (ðŸ”»{min_odds})</b>\n\n"  # Primera lÃ­nea en mayÃºsculas y negrita
            "{teams}\n"
            "{tournament}\n"
            "{date}\n\n"
            "{link}"
        )
        
    # Escapar caracteres especiales
    def safe_escape(self, text):
        if text is None:
            return ''
        text = str(text).strip()
        return html.escape(text, quote=False)

    def _get_cache_key(self, apuesta: dict, contrapartida: dict, profit: float) -> str:
        return f"{apuesta['teams'][0]}:{apuesta['teams'][1]}:{apuesta['time']}:{profit}"

    def clean_text(self, text: str) -> str:
        """
        Limpia y formatea el texto aplicando los reemplazos y eliminando palabras no deseadas.
        """
        if not text:
            return ''

        # Convertir a minÃºsculas y eliminar espacios extra
        text = str(text).strip().lower()

        # Definir patrÃ³n para palabras a eliminar (individuales o compuestas)
        words_to_remove = '|'.join(map(re.escape, self.words_to_remove))
        pattern = rf'\b({words_to_remove})\b'

        # Eliminar palabras no deseadas
        text = re.sub(pattern, '', text)

        # Aplicar reemplazos
        for old, new in self.replacements.items():
            text = text.replace(old.lower(), new.lower())

        # Eliminar espacios extra generados por las eliminaciones
        text = ' '.join(text.split())

        # Escapar caracteres especiales para Telegram HTML
        return html.escape(text, quote=False)


    def format_date(self, timestamp: int) -> str:
        try:
            if not timestamp:
                return ""
                
            # Convertimos el timestamp
            seconds = int(str(timestamp)[:-3])
            
            # Creamos el objeto datetime en UTC
            event_time = datetime.fromtimestamp(seconds, UTC)
            
            # Convertimos a la zona horaria de EspaÃ±a
            tz_spain = pytz.timezone("Europe/Madrid")
            event_time_spain = event_time.astimezone(tz_spain)

            # Formateamos cada componente por separado
            fecha = html.escape(event_time_spain.strftime('%d/%m/%Y'), quote=False)
            hora = html.escape(event_time_spain.strftime('%H:%M'), quote=False)
            dia = html.escape(self.dias[event_time_spain.weekday()], quote=False)

            # Devolvemos el formato sin necesidad de escapar parÃ©ntesis
            return f"ðŸ“… {fecha} ({dia} {hora})"
            
        except Exception as e:
            self.logger.error(f"Error formatting date: {e}")
            return ""

    def get_stake(self, profit: float, contrapartida_bk: str) -> str:

        logger.info(f"Analizando casa de apuestas: '{contrapartida_bk}' | Valor original: {repr(contrapartida_bk)}")
        
        contrapartida_bk = re.sub(r'\s+', '', str(contrapartida_bk).lower().strip())
        logger.info(f"Casa normalizada: '{contrapartida_bk}'")

        if contrapartida_bk == 'pinnaclesports':
            logger.info("Coincide con reglas de Pinnacle")
            # Rangos de Pinnacle son mÃ¡s estrictos
            if profit < -1:
                return ""
            if -1 <= profit <= -0.5:
                return "ðŸ”´"
            elif -0.5 < profit <= 1.5:
                return "ðŸŸ "
            elif 1.5 < profit <= 4:
                return "ðŸŸ¡"
            return "ðŸŸ¢"
            
        elif re.search(r'bet\s*365', contrapartida_bk, re.IGNORECASE):  # ComparaciÃ³n mÃ¡s flexible
            logger.info("Coincide con reglas de Bet365")
            # Bet365 permite rangos mÃ¡s amplios
            if profit >= 2:
                return "ðŸŸ " 
            else:
                return ""  
        
        else:
            logger.warning(
                f"Casa no reconocida:\n"
                f"Original: '{contrapartida_bk}'\n"
                f"Normalizada: '{contrapartida_bk}'\n"
                f"Hex: {contrapartida_bk.encode('utf-8').hex()}"
            )

        return ""
    
        
    def calculate_min_odds(self, value: float, contrapartida_bk:str) -> float:
        try:
            margin = 1.04
            prob_contraria = 1 / float(value)
            if contrapartida_bk == 'pinnaclesports':
                oddmin = 1 / (margin - prob_contraria - (1/100))
            elif contrapartida_bk == 'bet365':
                oddmin = 1 / (margin - prob_contraria - (0.5/100))
            return round(oddmin, 2)
        except Exception:
            return 0.0
        

    def ajustar_dominio(self, url: str) -> str:
        """Cambia el dominio de Bet365 de .com a .es y convierte la ruta a mayÃºsculas.
        Cambia el dominio de Betway de .com/en a .es/es.
        Cambia el dominio de bwin de .com/en a .es/es.
        Cambia el dominio de PokerStars de .uk a .es
        """
        if not url:
            return ""
            
        # Si es un enlace de bet365 (ya sea .com o .es)
        if "bet365" in url:
            # Primero normalizamos a .es si es necesario
            url = url.replace("bet365.com", "bet365.es")
            
            # Dividimos por .es para separar el dominio de la ruta
            parts = url.split(".es")
            
            if len(parts) > 1:
                # La primera parte es el dominio, la segunda es la ruta
                domain = parts[0]
                path = parts[1]
                
                # Convertimos la ruta a mayÃºsculas manteniendo el dominio igual
                return f"{domain}.es{path.upper()}"
        
        # Si es un enlace de betway
        elif "betway" in url:
            # Reemplazamos el dominio .com/en por .es/es
            url = url.replace("sports.betway.com/en/sports", "sports.betway.es/es/sports")
            
        # Si es un enlace de bwin
        elif "bwin" in url:
            url = url.replace("sports.bwin.com/en/", "sports.bwin.es/es/")
            
        # Si es un enlace de versus (con sportswidget)
        elif "sportswidget.versus.es" in url:
            url = url.replace("sportswidget.versus.es/sports", "www.versus.es/apuestas/sports")
        
        # Si es un enlace de versus (sin sportswidget)
        elif "versus.es/sports" in url:
            url = url.replace("versus.es/sports", "www.versus.es/apuestas/sports")

        # Si es un enlace de PokerStars
        elif "pokerstars" in url:
            url = url.replace("pokerstars.uk/", "pokerstars.es/")
            
        return url
    
    
    async def format_message(self, apuesta: dict, contrapartida: dict, profit: float) -> str:
        try:
            # Primero verificamos la cachÃ©
            cache_key = self._get_cache_key(apuesta, contrapartida, profit)
            cached = self._message_cache.get(cache_key)
            if cached:
                return cached

            # Validamos la fecha
            formatted_date = self.format_date(apuesta.get('time', 0))
            if not formatted_date:
                return ""

            # Obtenemos el bookmaker de contrapartida y su valor
            contrapartida_bk = contrapartida.get('bk', '')
            contrapartida_value = float(contrapartida.get('value', 0))

            # Obtenemos el stake basado en el profit y bookmaker
            stake = self.get_stake(profit, contrapartida_bk)
            if not stake:
                return ""
            
            # Calculamos min odds
            min_odds = self.calculate_min_odds(contrapartida_value, contrapartida_bk)
            

            # Procesamos el type_info
            type_parts = []
            type_dict = apuesta.get('type', {})

            for key in ['type', 'condition', 'variety', 'base', 'game', 'period']:
                value = type_dict.get(key, '')
                if value:
                    # Si el campo es 'condition', tratamos especÃ­ficamente los caracteres conflictivos
                    if key == 'condition':
                        cleaned_value = self.clean_text(str(value))  # Limpieza bÃ¡sica
                        # Eliminar escapado de puntos
                        cleaned_value = cleaned_value.replace("\\.", ".")
                    else:
                        # Limpia como cualquier otra parte
                        cleaned_value = self.clean_text(str(value))
                    
                    if cleaned_value:
                        type_parts.append(cleaned_value)

            # Combina las partes y convierte a mayÃºsculas
            type_info = ' '.join(type_parts).upper()
            type_info_fixed = (
                type_info
                .replace("\\.", ".")
                .replace(".\\", ".")
                .replace("\\-", "-")
                .replace("-\\", "-")
                .replace("\\(", "(")
                .replace("(\\", "(")
                .replace("\\)", ")")
                .replace(")\\", ")")
                .replace("\\", "")

            )



            
            team1 = self.clean_text(apuesta.get('teams', ['', ''])[0]).title()
            team2 = self.clean_text(apuesta.get('teams', ['', ''])[1]).title()
            teams = f"{self.emoji_cache.get(apuesta.get('sport_id', '').lower(), '')} <code>{team1}</code> vs <code>{team2}</code>"

            tournament = f"ðŸ† {self.clean_text(apuesta.get('tournament', '')).title()} ({self.clean_text(apuesta.get('sport_id', '')).title()})"
            tournament_fixed = (
                tournament
                .replace("\\.", ".")
                .replace(".\\", ".")
                .replace("\\-", "-")
                .replace("-\\", "-")
                .replace("\\(", "(")
                .replace("(\\", "(")
                .replace("\\)", ")")
                .replace(")\\", ")")
                .replace("\\", "")
            )
            
            link_original = apuesta.get('preferred_nav', {}).get('links', [{}])[0].get('link', {}).get('url', '')
            link_ajustado = self.ajustar_dominio(link_original)


            # Construimos el mensaje con el template
            result = self.message_template.format(
                stake=html.escape(str(stake), quote=False),
                type_info=html.escape(str(type_info_fixed), quote=False),
                odds=html.escape(str(apuesta.get('value', '')), quote=False),
                min_odds=html.escape(str(min_odds), quote=False),  
                teams=teams,
                tournament=html.escape(str(tournament_fixed), quote=False),
                date=formatted_date,  # Ya estÃ¡ escapado en format_date
                link=f'ðŸ”— <a href="{html.escape(link_ajustado, quote=True)}">{html.escape(link_ajustado, quote=False)}</a>'
                )

            if result:
                await self._message_cache.set(cache_key, result)
                
            return result

        except Exception as e:
            self.logger.error(f"Error al formatear el mensaje: {e}", exc_info=True)
            return ""
           
        
# Envio por Telegram
class TelegramSender:
    def __init__(self, tokens: List[str]):
        self.bots = []
        for token in tokens:
            bot = Bot(token=token)
            self.bots.append(bot)
        
        self.current_bot_index = 0
        self.message_queue = asyncio.PriorityQueue()
        self.retry_delay = 1
        self.max_retries = 3
        self.sending_semaphore = asyncio.Semaphore(30)
        self.failed_messages = {}
        self.retry_delays = {
            1: 1,    # 1er reintento: 1 segundo
            2: 5,    # 2do reintento: 5 segundos
            3: 15,   # 3er reintento: 15 segundos
        }
        self.max_wait_time = 30  # 30 segundos mÃ¡ximo

        # Nuevas variables para optimizaciÃ³n
        self._bot_locks = {bot: asyncio.Lock() for bot in self.bots}
        self._rate_limit_window = 1.0
        self._messages_per_window = 30
        self._message_timestamps = collections.deque(maxlen=self._messages_per_window)

    async def _enforce_rate_limit(self):
        current_time = time.time()
        
        while (self._message_timestamps and 
               current_time - self._message_timestamps[0] > self._rate_limit_window):
            self._message_timestamps.popleft()
        
        if len(self._message_timestamps) >= self._messages_per_window:
            wait_time = self._rate_limit_window - (current_time - self._message_timestamps[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self._message_timestamps.append(current_time)

    
    async def process_message_queue(self):
        while True:
            try:
                priority, (channel_id, message, retries) = await self.message_queue.get()
                
                if retries >= self.max_retries:
                    logger.error(f"Max retries reached for message to channel {channel_id}")
                    continue

                success = await self.send_message_optimized(channel_id, message)
                
                if not success:
                    # Reintentar con menor prioridad
                    await self.message_queue.put((priority + 1, (channel_id, message, retries + 1)))

                     
                
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

    async def send_message_optimized(self, channel_id: int, message: str) -> bool:
        start_time = time.time()
        tried_bots = set()
        
        # Mapeo de canales a nombres para logging mÃ¡s descriptivo
        channel_names = {
            REDACTED_CHANNEL_ID_1: "retabet_apuestas",
            REDACTED_CHANNEL_ID_2: "bet365",
            REDACTED_CHANNEL_ID_3: "winamax_es",
            REDACTED_CHANNEL_ID_4: "yaasscasino",
            REDACTED_CHANNEL_ID_5: "bwin",
            REDACTED_CHANNEL_ID_6: 'sportium',
            #REDACTED_CHANNEL_ID_8: 'caliente',
            REDACTED_CHANNEL_ID_9: 'betway',
            REDACTED_CHANNEL_ID_11: 'versus'
        }
        
        channel_name = channel_names.get(channel_id, str(channel_id))
        max_attempts_per_bot = 3
        
        while len(tried_bots) < len(self.bots):
            try:
                # Verificar si hemos excedido el tiempo mÃ¡ximo de espera
                elapsed_time = time.time() - start_time
                if elapsed_time > self.max_wait_time:
                    logger.warning(
                        f"Mensaje descartado despuÃ©s de {elapsed_time:.2f}s de intentos. "
                        f"Canal: {channel_name}"
                    )
                    return False

                # Obtener el prÃ³ximo bot a usar
                bot = self.bots[self.current_bot_index]
                bot_id = bot.token.split(':')[0]

                # Si ya hemos intentado con este bot, pasar al siguiente
                if bot_id in tried_bots:
                    self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                    continue

                # Aplicar rate limit
                await self._enforce_rate_limit()

                # Intentar enviar el mensaje
                await bot.send_message(
                    chat_id=channel_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    disable_notification=True
                )
                return True

            except TelegramRetryAfter as e:
                # Registrar el intento con este bot
                tried_bots.add(bot_id)
                
                logger.warning(
                    f"Rate limit alcanzado:\n"
                    f"- Bot: {bot_id}\n"
                    f"- Canal: {channel_name}\n"
                    f"- Tiempo de espera: {e.retry_after}s\n"
                    f"- Bots intentados: {len(tried_bots)}/{len(self.bots)}"
                )
                
                # Cambiar al siguiente bot
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                
                # Si hemos intentado con todos los bots, esperar un poco
                if len(tried_bots) == len(self.bots):
                    wait_time = min(e.retry_after, 30)
                    await asyncio.sleep(wait_time)
                    tried_bots.clear()  # Reiniciar intentos despuÃ©s de esperar

            except TelegramBadRequest as e:
                logger.error(
                    f"Error de formato en mensaje:\n"
                    f"- Bot: {bot_id}\n"
                    f"- Canal: {channel_name}\n"
                    f"- Error: {str(e)}"
                )
                return False  # No reintentar si el mensaje estÃ¡ mal formateado

            except TelegramForbiddenError:
                logger.error(
                    f"Bot sin acceso al canal:\n"
                    f"- Bot: {bot_id}\n"
                    f"- Canal: {channel_name}"
                )
                tried_bots.add(bot_id)
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)

            except Exception as e:
                logger.error(
                    f"Error enviando mensaje:\n"
                    f"- Bot: {bot_id}\n"
                    f"- Canal: {channel_name}\n"
                    f"- Error: {str(e)}"
                )
                tried_bots.add(bot_id)
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                await asyncio.sleep(1)

        # Si llegamos aquÃ­, es que no pudimos enviar con ningÃºn bot
        logger.error(
            f"No se pudo enviar mensaje despuÃ©s de intentar con todos los bots:\n"
            f"- Canal: {channel_name}\n"
            f"- Tiempo total: {time.time() - start_time:.2f}s"
        )
        return False


    async def cleanup(self):
        """Limpia recursos del TelegramSender"""
        self.failed_messages.clear()
        # Cerrar cualquier conexiÃ³n pendiente de los bots
        for bot in self.bots:
            await bot.session.close()    

# Logica principal del bot
class BettingBot:
    def __init__(self, config: BotConfig):
        """
        Inicializa el BettingBot con la configuraciÃ³n centralizada.
        
        Args:
            config (BotConfig): Objeto de configuraciÃ³n con todos los parÃ¡metros
        """
        # ConfiguraciÃ³n bÃ¡sica y logging
        self._initialize_base_config(config)
        
        # OptimizaciÃ³n de workers basada en CPU
        self.num_validation_workers = max(multiprocessing.cpu_count() * 8, 32)
        self.num_redis_workers = max(multiprocessing.cpu_count() * 16, 64)
        self.num_telegram_workers = max(multiprocessing.cpu_count() * 12, 48)
        
        # Inicializar servicios en orden de dependencia
        self._initialize_core_services(config)
        
        # Inicializar servicios de mensajerÃ­a
        self._initialize_messaging_services(config) 

        # InicializaciÃ³n para multiprocesamiento
        self.num_processors = multiprocessing.cpu_count()
        
        # Colas para procesamiento paralelo
        self.validation_queue = asyncio.Queue(maxsize=10000)
        self.redis_queue = asyncio.Queue(maxsize=10000)
        self.telegram_queue = asyncio.Queue(maxsize=10000)

        # Inicializar semÃ¡foro para procesamiento de picks
        self.processing_semaphore = asyncio.Semaphore(config.CONCURRENT_PICKS * 16)
        
        # Registro de inicializaciÃ³n
        self._log_initialization_status()
        
       

        self.performance_stats = {
            'processed_picks': 0,
            'validation_time': [],
            'redis_time': [],
            'telegram_time': [],
            'last_stat_reset': time.time()
        }



    def _initialize_base_config(self, config: BotConfig) -> None:
        """Inicializa la configuraciÃ³n bÃ¡sica y el sistema de logging."""
        self.config = config
        
        # ConfiguraciÃ³n del logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Asegurarnos de que no hay handlers previos
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
        
        # Handler para Telegram
        if config.TELEGRAM_TOKENS and config.LOG_CHANNEL_ID:
            telegram_handler = TelegramLogHandler(
                bot_token=config.TELEGRAM_TOKENS[0],
                chat_id=config.LOG_CHANNEL_ID
            )
            telegram_handler.setFormatter(logging.Formatter(
                '%(levelname)s - %(message)s\n'
                'Location: %(pathname)s:%(lineno)d\n'
                'Time: %(asctime)s'
            ))
            logger.addHandler(telegram_handler)
        
        self.logger = logger

    def _initialize_core_services(self, config: BotConfig) -> None:
        self.connection_manager = ConnectionManager(config)
        self.request_queue = RequestQueue(config, self.connection_manager)
        self.concurrency_manager = ConcurrencyManager(config)
        self.prefetch_manager = OptimizedPrefetchManager(
            config,
            self.request_queue
        )
        self.redis_handler = RedisHandler()
        self.message_formatter = MessageFormatter()

    def _initialize_messaging_services(self, config: BotConfig) -> None:
        self.telegram_sender = TelegramSender(config.TELEGRAM_TOKENS)
        self.telegram_semaphore = asyncio.Semaphore(30)
        
        self.bots = {}
        for token in config.TELEGRAM_TOKENS:
            bot = Bot(token=token)
            bot._parse_mode = ParseMode.HTML
            self.bots[token] = bot

    def _log_initialization_status(self) -> None:
        self.logger.info("BettingBot initialized with the following configuration:")
        self.logger.info(f"API URL: {self.config.API_URL}")
        self.logger.info(f"Rate Limit: {self.config.REQUEST_RATE_LIMIT} req/sec")
        self.logger.info(f"Concurrent Requests: {self.config.CONCURRENT_REQUESTS}")
        self.logger.info(f"Concurrent Picks: {self.config.CONCURRENT_PICKS}")
        self.logger.info(f"Cache Size: {self.config.CACHE_MAX_SIZE}")
        self.logger.info(f"Bookmakers: {', '.join(self.config.BOOKMAKERS)}")

    async def start(self):
        """
        Inicia todos los servicios del bot de manera organizada.
        """
        self.background_tasks = []
        
        try:
                       
            # 2. Iniciar el request queue con su limpieza de cachÃ©
            await self.request_queue.start_cache_cleanup()
            
            # 3. Iniciar el prefetch manager optimizado
            await self.prefetch_manager.start_prefetching()
            
            # 4. Iniciar procesamiento de mensajes Telegram
            self.background_tasks.append(
                asyncio.create_task(
                    self.telegram_sender.process_message_queue(),
                    name="telegram_queue_processor"
                )
            )
            
            # 5. Iniciar limpieza general de cachÃ©s
            self.background_tasks.append(
                asyncio.create_task(
                    self.clean_up_cache(interval=300),
                    name="general_cache_cleanup"
                )
            )
            
            self.logger.info("Todos los servicios del bot iniciados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante el inicio de servicios: {e}")
            await self.cleanup()
            raise

    async def start_workers(self):
        """Inicia los workers para el procesamiento paralelo"""
        workers = []
        
        # Workers para validaciÃ³n
        for _ in range(self.num_validation_workers):
            workers.append(asyncio.create_task(
                self.validation_worker(),
                name=f"validation_worker_{_}"
            ))
            
        # Workers para Redis
        for _ in range(self.num_redis_workers):
            workers.append(asyncio.create_task(
                self.redis_worker(),
                name=f"redis_worker_{_}"
            ))
            
        # Workers para Telegram
        for _ in range(self.num_telegram_workers):
            workers.append(asyncio.create_task(
                self.telegram_worker(),
                name=f"telegram_worker_{_}"
            ))
            
        return workers

    async def validation_worker(self):
        """Worker para validaciÃ³n de picks"""
        while True:
            try:
                pick = await self.validation_queue.get()
                try:
                    if await self.validate_pick(pick):
                        await self.redis_queue.put(pick)
                except Exception as e:
                    self.logger.error(f"Error en validaciÃ³n: {e}")
                finally:
                    self.validation_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error crÃ­tico en validation_worker: {e}")
                await asyncio.sleep(1)

    async def redis_worker(self):
        """Worker para procesamiento Redis"""
        while True:
            try:
                pick = await self.redis_queue.get()
                try:
                    if not isinstance(pick, dict) or 'prongs' not in pick:
                        continue

                    prong_1, prong_2 = pick['prongs']
                    bet_roles = self.determine_bet_roles(prong_1, prong_2)
                    
                    if not bet_roles:
                        continue
                        
                    contrapartida, apuesta, target_bookmaker = bet_roles
                    
                    pick_data = {
                        'teams': apuesta['teams'],
                        'time': apuesta['time'],
                        'type': apuesta['type'],
                        'contrapartida': contrapartida,
                        'apuesta': apuesta,
                        'profit': pick.get('profit', 0),
                        'target_bookmaker': target_bookmaker,
                        'tournament': apuesta.get('tournament', ''),
                        'sport_id': apuesta.get('sport_id', '')
                    }

                    sent_status = await self.redis_handler.is_pick_sent_batch([pick_data])
                    key = self.redis_handler._get_complete_key(pick_data)
                        
                    if not sent_status.get(key, False):
                        guardado_exitoso = await self.redis_handler.mark_picks_sent_batch([pick_data])
                        if guardado_exitoso:
                            await self.telegram_queue.put(pick_data)
                            # Guardar en PostgreSQL
                            

                except Exception as e:
                    self.logger.error(f"Error en Redis: {e}", exc_info=True)
                finally:
                    self.redis_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error crÃ­tico en redis_worker: {e}")
                await asyncio.sleep(1)

    async def telegram_worker(self):
        """Worker para envÃ­o Telegram"""
        while True:
            try:
                pick_data = await self.telegram_queue.get()
                try:
                    if isinstance(pick_data, dict) and 'apuesta' in pick_data and 'contrapartida' in pick_data:
                        message = await self.message_formatter.format_message(
                            pick_data['apuesta'],
                            pick_data['contrapartida'],
                            pick_data.get('profit', 0)
                        )
                        if message:
                            await self.telegram_sender.send_message_optimized(
                                channel_id=self.config.BOOKMAKER_CHANNELS[pick_data['target_bookmaker']],
                                message=message
                            )
                except Exception as e:
                    self.logger.error(f"Error en Telegram: {e}", exc_info=True)
                finally:
                    self.telegram_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error crÃ­tico en telegram_worker: {e}")
                await asyncio.sleep(1)

    async def validate_pick(self, surebet: dict) -> bool:
        """Valida un pick de forma asÃ­ncrona"""
        try:
            if not surebet or 'prongs' not in surebet or len(surebet['prongs']) != 2:
                return False

            prong_1, prong_2 = surebet['prongs']
            profit = surebet.get('profit')

            # Validar profit
            if profit is None or not (-1 <= profit <= 25):
                return False

            # Validar cuotas
            if not (self.config.MIN_ODDS <= float(prong_1['value']) <= self.config.MAX_ODDS and 
                    self.config.MIN_ODDS <= float(prong_2['value']) <= self.config.MAX_ODDS):
                return False

            # Determinar roles
            bet_roles = self.determine_bet_roles(prong_1, prong_2)
            if not bet_roles:
                return False

            contrapartida, apuesta, target_bookmaker = bet_roles

            # Validar tiempo del evento
            tz_spain = pytz_timezone("Europe/Madrid")
            event_time = datetime.fromtimestamp(
                int(str(apuesta['time'])[:-3]),
                tz=UTC
            ).astimezone(tz_spain)
            
            current_time = datetime.now(tz_spain)
            if (event_time - current_time).total_seconds() < self.config.MIN_EVENT_TIME:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error en validaciÃ³n de pick: {e}")
            return False

    def determine_bet_roles(self, prong_1: dict, prong_2: dict) -> Optional[Tuple[dict, dict, str]]:
        bk1, bk2 = prong_1['bk'], prong_2['bk']
        
        # Verificar si alguno es una casa objetivo
        target_bookies = set(self.config.TARGET_BOOKIES)
        if bk1 in target_bookies or bk2 in target_bookies:
            # Determinar cuÃ¡l es la casa objetivo y cuÃ¡l la contrapartida
            if bk1 in target_bookies:
                apuesta, contrapartida = prong_1, prong_2
            else:
                apuesta, contrapartida = prong_2, prong_1
                
            # Verificar si la contrapartida estÃ¡ permitida para esta casa
            allowed_contrapartidas = self.config.BOOKIE_CONTRAPARTIDAS.get(apuesta['bk'], [])
            if contrapartida['bk'] in allowed_contrapartidas:
                return contrapartida, apuesta, apuesta['bk']
                
        return None
    
    def prepare_pick_data(self, contrapartida: dict, apuesta: dict, pick: dict, target_bookmaker: str) -> dict:
        """Prepara los datos del pick para su procesamiento"""
        return {
            'teams': apuesta['teams'],
            'time': apuesta['time'],
            'type': apuesta['type'],
            'contrapartida': contrapartida,
            'apuesta': apuesta,
            'profit': pick.get('profit', 0),
            'target_bookmaker': target_bookmaker,
            'tournament': apuesta.get('tournament', ''),
            'sport_id': apuesta.get('sport_id', '')
        }
        

    async def process_picks(self):
        self.logger.info("Iniciando procesamiento de picks...")
        workers = await self.start_workers()
        
        try:
            while True:
                picks = await self.prefetch_manager.get_next_data()
                
                if picks:
                    batch_start = time.time()
                    batch_size = len(picks)
                    self.logger.info(f"Procesando nuevo batch de {batch_size} picks")
                    
                    valid_picks = [
                        pick for pick in picks 
                        if len(pick.get('prongs', [])) == 2
                    ]
                    
                    # Procesamiento en lotes mÃ¡s grandes
                    tasks = []
                    for pick in valid_picks:
                        task = asyncio.create_task(self.process_single_pick(pick))
                        tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                        
                    batch_time = time.time() - batch_start
                    self.logger.info(
                        f"Batch procesado en {batch_time:.2f}s. "
                        f"Velocidad: {batch_size/batch_time:.1f} picks/s"
                    )
                
                # Reducir intervalo de sleep
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            raise

    async def process_single_pick(self, pick):
        """Procesa un Ãºnico pick de manera optimizada"""
        start_time = time.time()
        
        try:
            # ValidaciÃ³n
            validation_start = time.time()
            if not await self.validate_pick(pick):
                return
            self.performance_stats['validation_time'].append(time.time() - validation_start)
            
            # Redis
            redis_start = time.time()
            if not isinstance(pick, dict) or 'prongs' not in pick:
                return
                
            prong_1, prong_2 = pick['prongs']
            bet_roles = self.determine_bet_roles(prong_1, prong_2)
            if not bet_roles:
                return
                
            contrapartida, apuesta, target_bookmaker = bet_roles
            pick_data = self.prepare_pick_data(contrapartida, apuesta, pick, target_bookmaker)
            
            sent_status = await self.redis_handler.is_pick_sent_batch([pick_data])
            key = self.redis_handler._get_complete_key(pick_data)
            
            if not sent_status.get(key, False):
                if await self.redis_handler.mark_picks_sent_batch([pick_data]):
                    self.performance_stats['redis_time'].append(time.time() - redis_start)
                    
                                        
                    # Telegram
                    telegram_start = time.time()
                    await self.telegram_queue.put(pick_data)
                    self.performance_stats['telegram_time'].append(time.time() - telegram_start)
            
            self.performance_stats['processed_picks'] += 1
            
                            
        except Exception as e:
            self.logger.error(f"Error processing pick: {e}")
            
            
    async def cleanup(self):
        """Limpieza ordenada de recursos"""
        try:
            # 1. Cancelar todas las tareas en segundo plano
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass


            # 3. Limpiar recursos en orden especÃ­fico
            cleanup_sequence = [
                (self.request_queue.cleanup, "RequestQueue"),
                (self.redis_handler.close, "Redis"),
                (self.connection_manager.cleanup, "ConnectionManager"),
                (self.telegram_sender.cleanup, "TelegramSender"),
                (self.prefetch_manager.cleanup, "PrefetchManager")
            ]
            
            for cleanup_func, resource_name in cleanup_sequence:
                try:
                    await cleanup_func()
                    self.logger.info(f"{resource_name} cerrado correctamente")
                except Exception as e:
                    self.logger.error(f"Error cerrando {resource_name}: {e}")

            # 4. Limpiar colas
            for queue in [self.validation_queue, self.redis_queue, self.telegram_queue]:
                while not queue.empty():
                    try:
                        queue.get_nowait()
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        break

            self.logger.info("Limpieza completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error durante la limpieza general: {e}")
            raise

    async def clean_up_cache(self, interval: int = 300):
        """
        Limpia periÃ³dicamente las cachÃ©s del sistema.
        
        Args:
            interval (int): Intervalo en segundos entre limpiezas (default: 300 segundos / 5 minutos)
        """
        try:
            while True:
                await asyncio.sleep(interval)
                self.logger.info("Iniciando limpieza programada de cachÃ©s...")
                
                try:
                    # Forzar recolecciÃ³n de basura de Python
                    gc.collect()
                    
                except Exception as e:
                    self.logger.error(f"Error durante la limpieza de cachÃ©s: {e}")
                    
        except asyncio.CancelledError:
            self.logger.info("Tarea de limpieza de cachÃ© cancelada")
            raise
        except Exception as e:
            self.logger.error(f"Error en tarea de limpieza de cachÃ©: {e}")
            raise

    async def send_telegram_message(self, message: str, bookmaker: str):
        """MÃ©todo para enviar mensajes a Telegram de forma segura"""
        if not message or not bookmaker:
            return

        channel_id = self.config.BOOKMAKER_CHANNELS.get(bookmaker)
        if not channel_id:
            return

        try:
            async with self.telegram_semaphore:
                await self.telegram_sender.send_message_optimized(
                    channel_id=channel_id,
                    message=message
                )
        except Exception as e:
            self.logger.error(f"Error sending telegram message: {e}")
            # Agregar a cola de reintentos
            await self.telegram_sender.message_queue.put((1, (channel_id, message, 0)))

    def get_bookie_level(self, bookie: str) -> int:
        """Obtiene el nivel de jerarquÃ­a de una casa de apuestas"""
        try:
            return self.config.BOOKIE_HIERARCHY.index(bookie)
        except ValueError:
            return len(self.config.BOOKIE_HIERARCHY)

    async def fetch_picks_from_api(self):
        """
        Obtiene los picks de la API usando el sistema de peticiones.
        Ahora usa la configuraciÃ³n centralizada y el rate limiting optimizado.
        """
        try:
            picks = await self.request_queue.fetch_picks()
            
            if picks:
                self.logger.info(f"Recibidos {len(picks)} picks de la API")
            else:
                self.logger.warning("No se recibieron picks de la API")
                
            return picks
            
        except Exception as e:
            self.logger.error(f"Error fetching picks: {e}", exc_info=True)
            return []

async def main():
    config = BotConfig()
    bot = BettingBot(config)

    try:
        await bot.start()
        await bot.process_picks()
    except KeyboardInterrupt:
        logger.info("InterrupciÃ³n detectada, cerrando el bot...")
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")