# database.py
# Работа с PostgreSQL: история диалогов, пользователи

import os
import asyncpg
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

# Глобальный пул подключений
pool = None


async def init_db():
    """Создаём пул подключений и таблицы при старте бота."""
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    
    async with pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Таблица истории диалогов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Индекс для быстрого поиска истории по пользователю
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user 
            ON messages(user_id, created_at DESC)
        """)
    
    print("✅ База данных инициализирована")


async def save_user(user_id: int, username: str, first_name: str):
    """Сохраняем/обновляем пользователя."""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                username = $2,
                first_name = $3,
                last_active = NOW()
        """, user_id, username, first_name)


async def save_message(user_id: int, role: str, content: str):
    """Сохраняем сообщение в историю."""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO messages (user_id, role, content)
            VALUES ($1, $2, $3)
        """, user_id, role, content)


async def get_history(user_id: int, limit: int = 20) -> list:
    """Получаем последние N сообщений пользователя для контекста."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT role, content FROM messages
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, user_id, limit)
    
    # Переворачиваем — нужен хронологический порядок
    history = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    return history


async def clear_history(user_id: int):
    """Очищаем историю диалога (команда /reset)."""
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM messages WHERE user_id = $1", user_id)


async def get_stats() -> dict:
    """Статистика для админа."""
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_messages = await conn.fetchval("SELECT COUNT(*) FROM messages")
        active_today = await conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE last_active > NOW() - INTERVAL '1 day'
        """)
    
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "active_today": active_today
    }
