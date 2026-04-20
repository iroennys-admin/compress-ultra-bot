import aiosqlite
from datetime import datetime
import os

class Database:
    def __init__(self):
        self.db_path = "compress_bot.db"
        self.conn = None

    async def connect(self):
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            await self.init_tables()
            print("✅ SQLite conectado correctamente")
        except Exception as e:
            print(f"❌ Error conectando a SQLite: {e}")
            raise e

    async def init_tables(self):
        # Tabla de usuarios
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                plan TEXT DEFAULT 'FREE',
                plan_expiry TIMESTAMP,
                quality TEXT DEFAULT 'medium',
                total_compressions INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de cola de compresión
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS compression_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.conn.commit()
        print("✅ Tablas creadas/verificadas")

    async def get_user(self, user_id):
        try:
            async with self.conn.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    user_dict = dict(zip(columns, row))
                    return user_dict
                return None
        except Exception as e:
            print(f"Error en get_user: {e}")
            return None

    async def create_user(self, user_id, username, first_name):
        try:
            await self.conn.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            await self.conn.commit()
            print(f"✅ Usuario {user_id} registrado")
        except Exception as e:
            print(f"Error creando usuario: {e}")

    async def update_quality(self, user_id, quality):
        try:
            await self.conn.execute(
                'UPDATE users SET quality = ? WHERE user_id = ?',
                (quality, user_id)
            )
            await self.conn.commit()
            print(f"✅ Calidad actualizada para {user_id}: {quality}")
        except Exception as e:
            print(f"Error en update_quality: {e}")

    async def add_to_queue(self, user_id, file_id):
        try:
            await self.conn.execute('''
                INSERT INTO compression_queue (user_id, file_id, status)
                VALUES (?, ?, 'pending')
            ''', (user_id, file_id))
            await self.conn.commit()
        except Exception as e:
            print(f"Error en add_to_queue: {e}")

    async def get_queue_position(self, user_id):
        try:
            async with self.conn.execute('''
                SELECT COUNT(*) FROM compression_queue 
                WHERE status = 'pending' AND id < (
                    SELECT id FROM compression_queue 
                    WHERE user_id = ? AND status = 'pending' 
                    ORDER BY id LIMIT 1
                )
            ''', (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            print(f"Error en get_queue_position: {e}")
            return 0

    async def update_stats(self, user_id, file_size):
        try:
            await self.conn.execute('''
                UPDATE users 
                SET total_compressions = total_compressions + 1,
                    total_size = total_size + ?
                WHERE user_id = ?
            ''', (file_size, user_id))
            await self.conn.commit()
            print(f"✅ Estadísticas actualizadas para {user_id}")
        except Exception as e:
            print(f"Error en update_stats: {e}")

    async def close(self):
        if self.conn:
            await self.conn.close()
            print("✅ Conexión SQLite cerrada")

db = Database()
