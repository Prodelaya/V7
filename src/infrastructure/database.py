
import aiosqlite
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "bot_data.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes the database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    service_name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)
            await db.commit()
            logger.info("Database initialized.")

    async def add_user(self, telegram_id: int, username: str, first_name: str, is_admin: bool = False):
        """Adds or updates a user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (telegram_id, username, first_name, is_admin)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    is_admin = MAX(users.is_admin, excluded.is_admin)
            """, (telegram_id, username, first_name, is_admin))
            await db.commit()

    async def get_user_subscriptions(self, telegram_id: int) -> List[Dict]:
        """Retrieves active subscriptions for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT service_name, start_date, end_date 
                FROM subscriptions 
                WHERE user_id = ? AND is_active = 1
            """, (telegram_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_subscription(self, telegram_id: int, service_name: str, start_date: str, end_date: str):
        """Adds a subscription."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO subscriptions (user_id, service_name, start_date, end_date)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, service_name, start_date, end_date))
            await db.commit()

    # --- Admin Queries ---

    async def get_all_clients_with_subs(self) -> List[Dict]:
        """Retrieves all users and their active subscriptions."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Get all users
            async with db.execute("SELECT telegram_id, username, first_name FROM users") as cursor:
                users = await cursor.fetchall()
            
            clients = []
            for user in users:
                user_dict = dict(user)
                start_date = None
                end_date = None
                
                # Get subs for this user
                subs = await self.get_user_subscriptions(user_dict["telegram_id"])
                active_subs = [s["service_name"] for s in subs]
                
                if subs:
                     # For display purposes simplifiction, take the latest end date
                     start_date = subs[0]["start_date"]
                     end_date = subs[0]["end_date"]

                clients.append({
                    "name": user_dict["first_name"],
                    "username": f"@{user_dict['username']}" if user_dict['username'] else "Sin alias",
                    "id": user_dict["telegram_id"],
                    "active": active_subs,
                    "start": start_date,
                    "end": end_date
                })
            return clients
