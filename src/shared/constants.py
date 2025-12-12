"""Global constants.

Contains:
- Stake emojis
- Date format strings
- Other constants used across the application

Reference: docs/04-Structure.md
"""

# Stake indicator emojis (from SRS RF-005)
STAKE_EMOJIS = {
    "low": "🔴",
    "medium_low": "🟠",
    "medium_high": "🟡",
    "high": "🟢",
}

# Spanish day names for date formatting
SPANISH_DAYS = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

# Date format for messages
DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"

# Timezone for event times
TIMEZONE = "Europe/Madrid"

# Redis key prefixes
REDIS_PREFIX_PICK = "pick:"
REDIS_PREFIX_CURSOR = "retador:cursor"

# API defaults
DEFAULT_ORDER = "created_at_desc"
DEFAULT_MIN_PROFIT = -1
DEFAULT_LIMIT = 5000
