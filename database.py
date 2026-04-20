import asyncio
import asyncpg
from datetime import datetime, timedelta
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.init_tables()

    async def init_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    plan TEXT DEFAULT 'FREE',
                    plan_expiry TIMESTAMP,
                    quality TEXT DEFAULT 'medium',
                    total_compressions INT DEFAULT 0,
                    total_size BIGINT DEFAULT 0,
                    joined_date TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS compression_queue (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                'SELECT * FROM users WHERE user_id = $1', user_id
            )

    async def create_user(self, user_id, username, first_name):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            ''', user_id, username, first_name)

    async def update_quality(self, user_id, quality):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET quality = $1 WHERE user_id = $2',
                quality, user_id
            )

    async def add_to_queue(self, user_id, file_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO compression_queue (user_id, file_id) VALUES ($1, $2)',
                user_id, file_id
            )

    async def get_queue_position(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchval('''
                SELECT COUNT(*) FROM compression_queue 
                WHERE status = 'pending' AND id < (
                    SELECT id FROM compression_queue 
                    WHERE user_id = $1 AND status = 'pending' 
                    ORDER BY id LIMIT 1
                )
            ''', user_id)

db = Database()
