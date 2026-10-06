"""
database.py — модуль для работы с базой данных бота.
Хранит историю всех диалогов с пользователями.
"""

import aiosqlite
from datetime import datetime


# Путь к файлу базы данных (создастся автоматически)
DB_PATH = "bot_history.db"


async def init_db():
    """Создаёт таблицу для истории сообщений, если её ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print("✅ База данных готова")


async def save_message(user_id: int, username: str, first_name: str, role: str, content: str):
    """Сохраняет сообщение в базу данных."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, username, first_name, role, content) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, role, content)
        )
        await db.commit()


async def get_user_history(user_id: int, limit: int = 20):
    """Возвращает последние N сообщений конкретного пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content, timestamp FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return rows[::-1]  # возвращаем в хронологическом порядке


async def get_all_users():
    """Возвращает список всех пользователей, которые писали боту."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT DISTINCT user_id, username, first_name, MAX(timestamp) as last_seen 
            FROM messages 
            GROUP BY user_id 
            ORDER BY last_seen DESC
        """)
        rows = await cursor.fetchall()
        return rows