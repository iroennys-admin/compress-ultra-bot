import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Calidades disponibles
QUALITIES = {
    "low": "480p (Baja)",
    "medium": "720p (Media)",
    "high": "1080p (Alta)",
    "ultra": "4K (Ultra)"
}

# Configuración FFmpeg
FFMPEG_SETTINGS = {
    "low": "-c:v libx265 -crf 28 -preset fast -c:a aac -b:a 64k",
    "medium": "-c:v libx265 -crf 26 -preset medium -c:a aac -b:a 96k",
    "high": "-c:v libx265 -crf 24 -preset slow -c:a aac -b:a 128k",
    "ultra": "-c:v libx265 -crf 22 -preset slower -c:a aac -b:a 192k"
}
