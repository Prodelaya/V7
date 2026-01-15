
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
from typing import Set, Dict, List
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from src.infrastructure.database import DatabaseManager

# Load environment variables
load_dotenv()

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_IDS_STR = os.getenv("ADMIN_USER_IDS", "39779830")
ADMIN_USER_IDS: Set[int] = {int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(",") if uid.strip()}

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "bot_data.db"
WELCOME_GIF_PATH = "src/bot/media/welcome_glitch.gif"

# States for ConversationHandler
REQUEST_SERVICE_NAME = 1

# Mock Data (Services info remains static for now, only user data is persistent)
SERVICES = {
    "bet365": {
        "name": "Bet365",
        "price": "159,99€",
        "duration": "30 días",
        "yield_val": "6-10%",
        "volume": "Alto",
        "liquidity": "Alta",
        "desc": "La opción más popular. Valor constante y alta liquidez. 🟢"
    },
    "sportium": {
        "name": "Sportium",
        "price": "159,99€",
        "duration": "30 días",
        "yield_val": "8-12%",
        "volume": "Medio",
        "liquidity": "Media",
        "desc": "Excelente para diversificar. Cuotas competitivas. 🔴"
    },
    "winamax": {
        "name": "Winamax",
        "price": "159,99€",
        "duration": "30 días",
        "yield_val": "5-9%",
        "volume": "Alto",
        "liquidity": "Alta",
        "desc": "Margen bajo y buenas oportunidades. 🔴"
    },
    "bwin": {
        "name": "Bwin",
        "price": "159,99€",
        "duration": "30 días",
        "yield_val": "7-11%",
        "volume": "Medio-Alto",
        "liquidity": "Media",
        "desc": "Ideal para complementar con Bet365. 🟡"
    }
}

# --- Helpers ---

def calculate_days_left(end_date_str: str) -> str:
    """Calculates days remaining from today until end_date_str (YYYY-MM-DD)."""
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = end_date - today
        days = delta.days + 1 # +1 to include today
        
        if days < 0:
            return "Caducado"
        elif days == 0:
            return "Caduca hoy"
        else:
            return f"Quedan {days} días"
    except Exception:
        return "N/A"

def format_date_display(date_str: str) -> str:
    """Converts YYYY-MM-DD to DD/MM."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m")
    except:
        return "??"

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message with a menu based on user role."""
    user = update.effective_user
    user_id = user.id
    db: DatabaseManager = context.bot_data["db"]

    logger.info(f"User started bot: {user_id} ({user.username})")
    
    # Register/Update user in DB
    is_admin = user_id in ADMIN_USER_IDS
    await db.add_user(user_id, user.username, user.first_name, is_admin)

    # --- Video/Animation ---
    # Try sending animation if it's a fresh start command
    if update.message and os.path.exists(WELCOME_GIF_PATH):
        try:
             await update.message.reply_animation(
                 animation=open(WELCOME_GIF_PATH, "rb"),
                 caption="⚡️ **Street Value System** ⚡️",
                 parse_mode="Markdown"
             )
        except Exception as e:
            logger.error(f"Failed to send animation: {e}")


    keyboard = []
    
    if is_admin:
        logger.info(f"Admin access granted for {user_id}")
        welcome_text = f"🏙️ **Hola Boss {user.first_name}.**\n\nPanel de Control Street Value:"
        keyboard = [
            [InlineKeyboardButton("👥 Clientes", callback_data="admin_clients")],
            [InlineKeyboardButton("📄 Suscripciones Activas", callback_data="admin_subs")],
            [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Ver como Cliente", callback_data="menu_user")]
        ]
    else:
        welcome_text = (
            f"🏙️ **¡Bienvenido a Street Value, {user.first_name}!**\n\n"
            "Tu asistente personal para **Value Betting**. \n"
            "Gestiona tus suscripciones y accede a servicios exclusivos.\n\n"
            "¿Qué necesitas hoy?"
        )
        keyboard = [
            [InlineKeyboardButton("💎 Mis Suscripciones", callback_data="my_subs")],
            [InlineKeyboardButton("📋 Ver Servicios", callback_data="menu_services")],
            [InlineKeyboardButton("❓ Soporte / Ayuda", callback_data="help")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    # If we sent animation, send text as separate message, otherwise edit/reply
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Returns the user's Telegram ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Tu ID: `{user_id}`", parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    db: DatabaseManager = context.bot_data["db"]

    if data == "menu_user" or data == "back_to_main":
        welcome_text = (
            "🏙️ **Panel Principal Street Value**\n\n"
            "Selecciona una opción:"
        )
        keyboard = [
            [InlineKeyboardButton("💎 Mis Suscripciones", callback_data="my_subs")],
            [InlineKeyboardButton("📋 Ver Servicios", callback_data="menu_services")],
            [InlineKeyboardButton("❓ Soporte / Ayuda", callback_data="help")]
        ]
        if ADMIN_USER_IDS and user_id in ADMIN_USER_IDS:
             keyboard.append([InlineKeyboardButton("🔙 Volver a Admin", callback_data="back_to_admin")])

        await query.edit_message_text(text=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "back_to_admin":
        if user_id in ADMIN_USER_IDS:
            keyboard = [
                [InlineKeyboardButton("👥 Clientes", callback_data="admin_clients")],
                [InlineKeyboardButton("📄 Suscripciones Activas", callback_data="admin_subs")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats")],
                [InlineKeyboardButton("🏠 Ver como Cliente", callback_data="menu_user")]
            ]
            await query.edit_message_text(
                "🏙️ **Panel de Control Admin:**", 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    elif data == "my_subs":
        subs = await db.get_user_subscriptions(user_id)
        
        # DEMO Mode for Admin if empty
        if not subs and user_id in ADMIN_USER_IDS:
            user_subs_text = (
                "💎 **Tus Suscripciones Activas (DEMO):**\n\n"
                "✅ **Bet365**\n"
                "   📅 Expira: 15/02 (Quedan 30 días)\n"
                "   🚦 Estado: Activo\n\n"
                "ℹ️ *Estás viendo esto porque eres Admin.*"
            )
            keyboard_subs = [[InlineKeyboardButton("🔄 Renovar Bet365", callback_data="renew_bet365")]]
        elif subs:
             user_subs_text = "💎 **Tus Suscripciones Activas:**\n\n"
             keyboard_subs = []
             for s in subs:
                 end_date = s["end_date"]
                 days_left = calculate_days_left(end_date)
                 end_display = format_date_display(end_date)
                 svc_name = s["service_name"]
                 
                 user_subs_text += (
                    f"✅ **{svc_name}**\n"
                    f"   📅 Expira: {end_display} ({days_left})\n"
                    f"   🚦 Estado: Activo\n\n"
                 )
                 keyboard_subs.append([InlineKeyboardButton(f"🔄 Renovar {svc_name}", callback_data=f"renew_{svc_name}")])
        else:
             user_subs_text = "❌ No tienes suscripciones activas actualmente."
             keyboard_subs = []

        keyboard = keyboard_subs + [
            [InlineKeyboardButton("📋 Contratar Nuevo Servicio", callback_data="menu_services")],
            [InlineKeyboardButton("🔙 Volver", callback_data="back_to_main")]
        ]
        await query.edit_message_text(text=user_subs_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_services":
        keyboard = []
        for key, service in SERVICES.items():
            keyboard.append([InlineKeyboardButton(f"🔹 {service['name']}", callback_data=f"svc_{key}")])
        
        keyboard.append([InlineKeyboardButton("✨ Solicitar otra Bookie", callback_data="req_service_start")])
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_main")])
        
        await query.edit_message_text(
            text="📋 **Catálogo de Servicios**\n\nSelecciona una casa de apuestas:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("svc_"):
        service_key = data.split("_")[1]
        service = SERVICES.get(service_key)
        
        if service:
            text = (
                f"🏢 **SERVICIO: {service['name']}**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"💰 **Precio**: `{service['price']}`\n"
                f"⏱ **Duración**: `{service['duration']}`\n"
                f"📈 **Yield esperado**: `{service['yield_val']}`\n"
                f"📊 **Volumen**: `{service['volume']}`\n"
                f"💧 **Liquidez**: `{service['liquidity']}`\n\n"
                f"_{service['desc']}_"
            )
            keyboard = [
                [InlineKeyboardButton("✅ Contratar Ahora", callback_data=f"buy_{service_key}")],
                [InlineKeyboardButton("🔙 Volver al Catálogo", callback_data="menu_services")]
            ]
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "help":
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_main")]]
        await query.edit_message_text(
            text=(
                "☎️ **Atención al Cliente**\n\n"
                "Para cualquier consulta, incidencia o contratación manual:\n\n"
                "📧 **Email**: `streetvalueinfo@yahoo.es`\n"
                "👤 **Telegram**: @SoporteStreetValue"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data.startswith("buy_") or data.startswith("renew_"):
        action = "renovación" if data.startswith("renew_") else "contratación"
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_main")]]
        await query.edit_message_text(
            text=f"🚧 **Proceso de {action}** 🚧\n\n"
                 "Estamos finalizando la integración automática.\n"
                 "Por favor, escribe a `streetvalueinfo@yahoo.es` para proceder.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Admin Handlers
    elif data == "admin_clients":
        clients = await db.get_all_clients_with_subs()
        
        text = "👥 **Listado de Clientes (DB)**\n━━━━━━━━━━━━━━━━━━━\n"
        if not clients:
            text += "No hay clientes registrados en la base de datos aún."
        
        for c in clients:
            status = "🟢" if c["active"] else "⚪️"
            services = ", ".join(c["active"]) if c["active"] else "Inactivo"
            
            start_fmt = format_date_display(c["start"]) if c["start"] else "--/--"
            end_fmt = format_date_display(c["end"]) if c["end"] else "--/--"
            
            text += (
                f"{status} **{c['name']}** (`{c['username']}`)\n"
                f"   └ Svcs: {services}\n"
                f"   └ 📅 {start_fmt} ➡ {end_fmt}\n\n"
            )
            
        keyboard = [[InlineKeyboardButton("🔙 Volver a Admin", callback_data="back_to_admin")]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_subs":
        clients = await db.get_all_clients_with_subs()
        counts = {}
        for c in clients:
            for s in c["active"]:
                counts[s] = counts.get(s, 0) + 1
        
        text = "📄 **Resumen de Suscripciones**\n━━━━━━━━━━━━━━━━━━━\n"
        if not counts:
            text += "No hay suscripciones activas."
        else:
            for s_name, count in counts.items():
                text += f"🔹 **{s_name}**: {count} usuarios\n"
                
        keyboard = [[InlineKeyboardButton("🔙 Volver a Admin", callback_data="back_to_admin")]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_stats":
        text = (
            "📊 **Métricas del Mes**\n━━━━━━━━━━━━━━━━━━━\n"
            "🗓 **Octubre 2024**\n"
            "📈 **Nuevos Clientes**: +14\n"
            "💰 **Ingresos Brutos**: 3.450€\n"
            "📉 **Churn Rate**: 2.1%\n"
            "🔝 **Servicio Top**: Bet365"
        )
        keyboard = [[InlineKeyboardButton("🔙 Volver a Admin", callback_data="back_to_admin")]]
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# --- Service Request Conversation Handlers ---

async def req_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="req_cancel")]]
    await query.edit_message_text(
        text="✨ **Solicitud de Nueva Bookie**\n\nEscribe el nombre de la casa de apuestas:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return REQUEST_SERVICE_NAME

async def req_service_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    requested_bookie = update.message.text
    logger.info(f"REQUEST: {update.effective_user.id} asked for {requested_bookie}")
    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_services")]]
    await update.message.reply_text(
        f"✅ **¡Solicitud Recibida!**\n\nHemos anotado: **{requested_bookie}**.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def req_service_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [] # (Same keyboard logic as main menu services)
    for key, service in SERVICES.items():
            keyboard.append([InlineKeyboardButton(f"🔹 {service['name']}", callback_data=f"svc_{key}")])
    keyboard.append([InlineKeyboardButton("✨ Solicitar otra Bookie", callback_data="req_service_start")])
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_main")])
    
    await query.edit_message_text(text="📋 **Catálogo**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END


# --- Main ---

def main() -> None:
    """Run the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN provided.")
        return

    # Initialize DB Manager
    db = DatabaseManager(DB_PATH)
    
    application = Application.builder().token(TOKEN).build()
    
    # Store db in context
    application.bot_data["db"] = db

    # Run DB init on startup (trick: run it in an async hook or just ensure it exists)
    # Since Application.run_polling manages loop, best to use post_init
    async def post_init(app: Application):
        await app.bot_data["db"].init_db()
        logger.info("DB Initialized via post_init")
        # Pre-seed for demo (Optional)
        # await app.bot_data["db"].add_user(39779830, "@Yorerm", "Yorerm", True)

    application.post_init = post_init

    req_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(req_service_start, pattern="^req_service_start$")],
        states={
            REQUEST_SERVICE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_service_save),
                CallbackQueryHandler(req_service_cancel, pattern="^req_cancel$")
            ]
        },
        fallbacks=[CallbackQueryHandler(req_service_cancel, pattern="^req_cancel$")]
    )

    application.add_handler(req_conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot started successfully...")
    application.run_polling()


if __name__ == "__main__":
    main()
